import cv2
import numpy as np
import os
import sys

# =============================================================================
# 1. Пути к видеофайлам
# =============================================================================
input_video_path = 'tv_video.MOV'       # видео с телевизором
overlay_video_path = 'overlay_video.mp4' # вставляемое видео
output_video_path = 'output_video.mp4'   # результат

# =============================================================================
# 2. Функция для проверки существования файла и его открываемости
# =============================================================================
def check_video(path, description):
    if not os.path.exists(path):
        print(f"Файл {path} не найден.")
        new_path = input(f"Укажите правильный путь к {description} (или 'q' для выхода): ").strip()
        if new_path.lower() == 'q':
            sys.exit(0)
        return new_path
    # Пробуем открыть
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Не удалось открыть {path}. Попробуйте другой файл.")
        new_path = input(f"Укажите правильный путь к {description} (или 'q' для выхода): ").strip()
        if new_path.lower() == 'q':
            sys.exit(0)
        return new_path
    ret, _ = cap.read()
    cap.release()
    if not ret:
        print(f"Файл {path} повреждён или не читается.")
        new_path = input(f"Укажите правильный путь к {description} (или 'q' для выхода): ").strip()
        if new_path.lower() == 'q':
            sys.exit(0)
        return new_path
    return path

# =============================================================================
# 3. Функция для автоматического поиска четырёхугольника (экрана) на кадре
#    Возвращает упорядоченные точки или None, если не найдено/прервано.
# =============================================================================
def find_screen_quadrangle(frame):
    """
    Принимает цветной кадр (BGR).
    Пытается найти четырёхугольник.
    Возвращает упорядоченный список из 4 точек или None.
    Во время работы показывает окно с границами Canny.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    # Показываем границы (для отладки)
    cv2.imshow("Canny edges - press any key to switch to manual", edges)
    cv2.waitKey(1)  # необходимо для обновления окна

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Найдено контуров: {len(contours)}")
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for i, contour in enumerate(contours[:10]):
        area = cv2.contourArea(contour)
        print(f"Контур {i+1}: площадь {area:.0f} пикс.")
        if area < 0.05 * frame.shape[0] * frame.shape[1]:
            continue

        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) == 4:
            pts = approx.reshape(4, 2)
            ordered = order_points(pts)
            print("Найден четырёхугольник!")
            cv2.destroyWindow("Canny edges - press any key to switch to manual")
            return ordered

        # Проверяем, не нажал ли пользователь клавишу для прерывания
        if cv2.waitKey(1) != -1:
            print("Автоопределение прервано пользователем.")
            cv2.destroyWindow("Canny edges - press any key to switch to manual")
            return None

    print("Четырёхугольник не найден.")
    cv2.destroyWindow("Canny edges - press any key to switch to manual")
    return None

def order_points(pts):
    """Упорядочивает 4 точки: левый верх, правый верх, правый низ, левый низ."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

# =============================================================================
# 4. Функция для ручного выбора 4 углов (с подсказкой на изображении)
# =============================================================================
def manual_select_points(frame):
    """
    Отображает кадр и просит пользователя кликнуть 4 угла в порядке:
    левый верхний, правый верхний, правый нижний, левый нижний.
    Возвращает массив точек в этом порядке.
    """
    img = frame.copy()
    cv2.putText(img, "Click 4 corners: TL, TR, BR, BL", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(img, "After 4 clicks window closes", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    points = []

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(img, str(len(points)), (x+10, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Select corners", img)
            if len(points) == 4:
                cv2.destroyWindow("Select corners")

    cv2.imshow("Select corners", img)
    cv2.setMouseCallback("Select corners", mouse_callback)

    while len(points) < 4:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            sys.exit(0)

    cv2.destroyAllWindows()
    # Упорядочиваем на всякий случай
    return order_points(np.array(points))

# =============================================================================
# 5. Функция для воспроизведения готового видео
# =============================================================================
def play_video(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("Не удалось открыть видео для просмотра.")
        return
    print("Воспроизведение. Нажмите 'q' для выхода.")
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        cv2.imshow("Result", frame)
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

# =============================================================================
# 6. Основная программа
# =============================================================================
if __name__ == "__main__":
    # Проверка существования выходного файла
    if os.path.exists(output_video_path):
        print(f"Файл {output_video_path} уже существует.")
        ans = input("Воспроизвести (v), пересоздать (r) или выйти (q)? ").lower()
        if ans == 'v':
            play_video(output_video_path)
            sys.exit(0)
        elif ans == 'q':
            sys.exit(0)
        # иначе (r) продолжаем

    # Проверка исходных видео
    input_video_path = check_video(input_video_path, "видео с телевизором")
    overlay_video_path = check_video(overlay_video_path, "вставляемое видео")

    # Открываем видео
    cap_input = cv2.VideoCapture(input_video_path)
    cap_overlay = cv2.VideoCapture(overlay_video_path)

    # Читаем первый кадр для выбора углов
    ret, first_frame = cap_input.read()
    if not ret:
        print("Не удалось прочитать первый кадр.")
        sys.exit(1)

    # Получаем параметры видео
    fps = cap_input.get(cv2.CAP_PROP_FPS)
    width_input = int(cap_input.get(cv2.CAP_PROP_FRAME_WIDTH))
    height_input = int(cap_input.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap_input.get(cv2.CAP_PROP_FRAME_COUNT))
    width_overlay = int(cap_overlay.get(cv2.CAP_PROP_FRAME_WIDTH))
    height_overlay = int(cap_overlay.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Исходное видео: {width_input}x{height_input}, {fps} fps, {total_frames} кадров")
    print(f"Вставляемое видео: {width_overlay}x{height_overlay}")

    # Автоматическое определение углов
    print("Попытка автоматического поиска экрана...")
    print("(Если процесс затянется, нажмите любую клавишу в окне 'Canny edges' для перехода к ручному выбору)")
    points = find_screen_quadrangle(first_frame)

    if points is None:
        print("Автоопределение не удалось или прервано. Переход к ручному выбору.")
        points = manual_select_points(first_frame)
    else:
        print("Автоопределение успешно. Использую найденные углы.")

    # Подготовка к трекингу
    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    prev_pts = points.astype(np.float32).reshape(-1, 1, 2)

    lk_params = dict(winSize=(15,15), maxLevel=2,
                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    # Создание выходного видео
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width_input, height_input))

    # Основной цикл обработки
    frame_count = 0
    print("Обработка началась. Откроется окно с результатом. Нажмите 'q' для досрочного выхода.")

    while True:
        ret_input, frame_input = cap_input.read()
        if not ret_input:
            break

        ret_overlay, frame_overlay = cap_overlay.read()
        if not ret_overlay:
            cap_overlay.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret_overlay, frame_overlay = cap_overlay.read()
            if not ret_overlay:
                break

        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Обработано {frame_count}/{total_frames}")

        curr_gray = cv2.cvtColor(frame_input, cv2.COLOR_BGR2GRAY)
        curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, prev_pts, None, **lk_params)

        if status is not None:
            prev_pts[status == 1] = curr_pts[status == 1]

        current_corners = prev_pts.reshape(4, 2)

        # Гомография
        dst_pts = np.array([[0,0],
                            [width_overlay-1,0],
                            [width_overlay-1,height_overlay-1],
                            [0,height_overlay-1]], dtype=np.float32)
        src_pts = current_corners.astype(np.float32)
        H, _ = cv2.findHomography(dst_pts, src_pts)
        warped = cv2.warpPerspective(frame_overlay, H, (width_input, height_input))

        # Маска
        mask = np.sum(warped, axis=2) > 0
        mask = mask.astype(np.uint8) * 255

        # Наложение
        result = np.where(mask[..., None] == 255, warped, frame_input)

        out.write(result)
        prev_gray = curr_gray.copy()

        # Показываем результат в реальном времени
        cv2.imshow("Result (q to quit)", result)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Завершение
    cap_input.release()
    cap_overlay.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"Готово! Результат сохранён в {output_video_path}")

    # Предложение посмотреть
    if input("Посмотреть результат? (y/n): ").lower() == 'y':
        play_video(output_video_path)