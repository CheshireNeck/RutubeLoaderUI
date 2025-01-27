import os
import traceback
import threading
from tkinter import Tk, Label, Entry, Button, filedialog, Listbox, StringVar, messagebox
from yt_dlp import YoutubeDL


class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RuTube Video Downloader")
        self.root.geometry("800x600")

        self.download_queue = []  # Очередь ссылок
        self.current_download = None
        self.save_path = StringVar(value="Папка не выбрана")
        self.progress_vars = {}  # Прогресс каждой ссылки

        self.create_widgets()

    def create_widgets(self):
        # Поле ввода ссылки
        Label(self.root, text="Введите ссылку на RuTube видео:").pack(pady=5)
        self.link_input = Entry(self.root, width=50)
        self.link_input.pack(pady=5)

        # Кнопка выбора папки
        Button(self.root, text="Выбрать папку для сохранения", command=self.select_save_path).pack(pady=5)
        Label(self.root, textvariable=self.save_path).pack(pady=5)

        # Кнопка добавления ссылки
        Button(self.root, text="Добавить ссылку", command=self.add_to_queue).pack(pady=5)

        # Список очереди
        Label(self.root, text="Очередь ссылок:").pack(pady=5)
        self.queue_list = Listbox(self.root, height=10, width=100)
        self.queue_list.pack(pady=5)

        # Список прогресса
        Label(self.root, text="Прогресс загрузки:").pack(pady=5)
        self.progress_list = Listbox(self.root, height=10, width=50)
        self.progress_list.pack(pady=5)

    def select_save_path(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path.set(folder)

    def add_to_queue(self):
        url = self.link_input.get().strip()
        if not self.save_path.get() or self.save_path.get() == "Папка не выбрана":
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите папку для сохранения.")
            return

        if not url:
            messagebox.showwarning("Ошибка", "Введите ссылку на видео.")
            return

        # Проверяем дублирование ссылки
        if url in self.download_queue:
            messagebox.showinfo("Дубликат", "Эта ссылка уже добавлена в очередь.")
            return

        # Добавляем ссылку в очередь
        self.download_queue.append(url)
        index = len(self.download_queue)
        self.queue_list.insert('end', f"{index}. {url}")  # Пронумерованная ссылка
        self.progress_list.insert('end', f"{index}. Ожидание...")  # Номер ссылки и статус
        self.link_input.delete(0, 'end')

        # Запускаем загрузку автоматически
        if not self.current_download:
            self.start_download()

    def start_download(self):
        if not self.download_queue:
            return

        self.current_download = self.download_queue.pop(0)
        current_index = len(self.progress_vars) + 1  # Текущий индекс (по очереди)
        self.progress_vars[current_index] = 0  # Инициализация прогресса

        # Обновляем статус в списке прогресса
        self.progress_list.delete(current_index - 1)
        self.progress_list.insert(current_index - 1, f"{current_index}. Загрузка...")

        threading.Thread(target=self.download_video, args=(self.current_download, current_index), daemon=True).start()

    def download_video(self, url, index):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(self.save_path.get(), '%(title)s.%(ext)s'),
                'format': 'best',
                'hls_prefer_native': True,
                'noplaylist': True,
                'ignoreerrors': True,
                'progress_hooks': [lambda d: self.hook(d, index)],
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Обновляем статус завершения
            self.progress_list.delete(index - 1)
            self.progress_list.insert(index - 1, f"{index}. Завершено")

        except Exception as e:
            # Обновляем статус ошибки
            error_message = "Ошибка загрузки"
            self.progress_list.delete(index - 1)
            self.progress_list.insert(index - 1, f"{index}. {error_message}")
            print(f"Ошибка при загрузке {url}: {traceback.format_exc()}")

        finally:
            # Завершаем текущую загрузку и запускаем следующую
            self.current_download = None
            if self.download_queue:
                self.start_download()

    def hook(self, d, index):
        """Обработчик прогресса загрузки."""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0.0').strip()
            self.progress_list.delete(index - 1)
            self.progress_list.insert(index - 1, f"{index}. Загрузка: {percent}")
        elif d['status'] == 'finished':
            print(f"Ссылка {index} завершена.")


if __name__ == "__main__":
    root = Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()
