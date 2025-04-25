import os
import cv2
import time
import imageio
import tempfile
import shutil
import threading
from tkinter import filedialog
from PIL import Image
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

# Cartoon styles dictionary
STYLE_MAP = {
    "Default": None,
    "Comic": "COMIC",
    "Watercolor": "WATERCOLOR",
    "AI Anime": "AI_ANIME",
    "Pixar": "PIXAR"
}

# Cartoonify effect processor
def apply_cartoon_effect(frame, style="Default", cartoon_level=5):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(gray, 255,
                                  cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(frame, d=cartoon_level * 2 + 1, sigmaColor=200, sigmaSpace=200)
    cartoon = cv2.bitwise_and(color, color, mask=edges)

    if style == "COMIC":
        cartoon = cv2.stylization(frame, sigma_s=60, sigma_r=0.5)
    elif style == "WATERCOLOR":
        cartoon = cv2.edgePreservingFilter(frame, flags=1, sigma_s=60, sigma_r=0.4)
    elif style == "AI_ANIME":
        cartoon = cv2.detailEnhance(frame, sigma_s=10, sigma_r=0.15)
    elif style == "PIXAR":
        cartoon = cv2.detailEnhance(frame, sigma_s=100, sigma_r=0.25)

    return cartoon

class CartoonifyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cartoonify Pro By MTB")
        self.geometry("600x400")

        # Logo
        try:
            logo_img = ctk.CTkImage(Image.open("logo.png"), size=(60, 60))
            self.logo = ctk.CTkLabel(self, image=logo_img, text="")
            self.logo.pack(pady=5)
        except:
            pass

        # Input
        self.input_path = None
        self.output_path = None

        self.upload_btn = ctk.CTkButton(self, text="Upload Video", command=self.select_input)
        self.upload_btn.pack(pady=10)

        self.res_var = ctk.StringVar(value="720p")
        self.res_slider = ctk.CTkOptionMenu(self, values=["480p", "720p", "1080p"], variable=self.res_var)
        self.res_slider.pack(pady=5)

        self.cartoon_level_slider = ctk.CTkSlider(self, from_=1, to=10, number_of_steps=9, command=self.update_cartoon_level)
        self.cartoon_level_slider.set(5)
        self.cartoon_level_slider.pack(pady=5)

        self.style_option = ctk.CTkOptionMenu(self, values=list(STYLE_MAP.keys()))
        self.style_option.set("Default")
        self.style_option.pack(pady=5)

        self.save_btn = ctk.CTkButton(self, text="Select Output Folder & Start", command=self.select_output)
        self.save_btn.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.pack(pady=20)
        self.progress.set(0)

        self.cartoon_level = 5

    def update_cartoon_level(self, value):
        self.cartoon_level = int(float(value))

    def select_input(self):
        file = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi")])
        if file:
            self.input_path = file
            CTkMessagebox(title="Uploaded", message=f"Selected: {os.path.basename(file)}", icon="check")

    def select_output(self):
        if not self.input_path:
            CTkMessagebox(title="Error", message="Please select a video first!", icon="cancel")
            return

        folder = filedialog.askdirectory()
        if folder:
            filename = os.path.splitext(os.path.basename(self.input_path))[0] + "_cartoonified.mp4"
            self.output_path = os.path.join(folder, filename)
            thread = threading.Thread(target=self.cartoonify_video)
            thread.start()

    def cartoonify_video(self):
        cap = cv2.VideoCapture(self.input_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        res = self.res_var.get()
        style = self.style_option.get()

        if res == "480p": width, height = 640, 480
        elif res == "1080p": width, height = 1920, 1080
        else: width, height = 1280, 720

        fps = cap.get(cv2.CAP_PROP_FPS)

        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        writer = imageio.get_writer(temp_video.name, fps=fps)

        count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (width, height))
            cartoon = apply_cartoon_effect(frame, STYLE_MAP.get(style), self.cartoon_level)
            writer.append_data(cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB))

            count += 1
            self.progress.set(count / total)
            self.update_idletasks()

        writer.close()
        cap.release()
        temp_video.flush()
        temp_video.close()
        time.sleep(1)

        try:
            shutil.move(temp_video.name, self.output_path)
        except PermissionError:
            time.sleep(1.5)
            try:
                shutil.move(temp_video.name, self.output_path)
            except Exception as e:
                CTkMessagebox(title="Error", message=f"Couldn't save video: {e}", icon="cancel")

        if os.path.exists(temp_video.name):
            try:
                os.remove(temp_video.name)
            except:
                pass

        CTkMessagebox(title="Done", message="Cartoonified video saved!", icon="check")
        self.progress.set(0)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = CartoonifyApp()
    app.mainloop()
