import sys
import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk

class VideoApp:
    def __init__(self, window, window_title, video_source):
        self.window = window
        self.window.title(window_title)

        # Открываем видеопоток (камера или файл)
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            print("Не удалось открыть видеоисточник")
            sys.exit(1)

        # Получаем размеры первого кадра для установки размера окна
        ret, frame = self.vid.read()
        if ret:
            self.height, self.width = frame.shape[:2]
        else:
            self.height, self.width = 480, 640  # запасные значения

        # Создаем холст для отображения видео
        self.canvas = tk.Canvas(window, width=self.width, height=self.height)
        self.canvas.pack()

        # Привязываем обработчик клика мыши
        self.canvas.bind("<Button-1>", self.on_click)

        # Список точек для рисования прямоугольников
        self.points = []

        # Кнопки управления
        btn_frame = tk.Frame(window)
        btn_frame.pack()

        btn_reset = tk.Button(btn_frame, text="Сброс (C)", command=self.reset_points)
        btn_reset.pack(side=tk.LEFT, padx=5)

        btn_quit = tk.Button(btn_frame, text="Выход (Q)", command=self.quit_app)
        btn_quit.pack(side=tk.LEFT, padx=5)

        # Привязка клавиш к окну
        self.window.bind('<c>', lambda e: self.reset_points())
        self.window.bind('<C>', lambda e: self.reset_points())  # заглавная
        self.window.bind('<q>', lambda e: self.quit_app())
        self.window.bind('<Q>', lambda e: self.quit_app())

        # Обновление видео
        self.delay = 15  # мс между кадрами
        self.update()

        self.window.protocol("WM_DELETE_WINDOW", self.quit_app)

    def on_click(self, event):
        """Сохраняем координаты клика (относительно канваса)"""
        x, y = event.x, event.y
        # Проверяем, что клик в пределах изображения
        if 0 <= x < self.width and 0 <= y < self.height:
            self.points.append((x, y))
            print(f"Добавлена точка: ({x}, {y})")

    def reset_points(self):
        """Очистить список точек"""
        self.points.clear()
        print("Точки сброшены")

    def quit_app(self):
        """Завершение приложения"""
        self.vid.release()
        self.window.quit()
        self.window.destroy()

    def update(self):
        """Получение нового кадра и обновление холста"""
        ret, frame = self.vid.read()
        if ret:
            # Рисуем прямоугольники вокруг каждой точки
            for (x, y) in self.points:
                # Прямоугольник 20x20 с центром в точке клика
                cv2.rectangle(frame, (x-10, y-10), (x+10, y+10), (0, 255, 0), 2)
                # Можно также рисовать маленький круг в центре
                cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)

            # Конвертируем кадр в формат для Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        else:
            # Если видео закончилось, можно перемотать или остановить
            # Для файла можно перезапустить:
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, 0)
            # return

        self.window.after(self.delay, self.update)


if __name__ == "__main__":
    # Разбор аргументов командной строки
    if len(sys.argv) < 2:
        print("Использование: python script.py <источник_видео>")
        print("Пример: python script.py 0  (для веб-камеры)")
        print("Пример: python script.py video.mp4  (для файла)")
        sys.exit(1)

    source = sys.argv[1]
    # Если аргумент - число, используем как индекс камеры
    if source.isdigit():
        source = int(source)

    # Создаем окно Tkinter
    root = tk.Tk()
    app = VideoApp(root, "Отслеживание кликов мыши", source)
    root.mainloop()