"""
This example script is borrowed from the Mine Tool project at https://github.com/AlinaWan/mine-tool
"""
__version__ = '1.0.0-beta.1'
__author__ = 'Riri'
__license__ = 'MPL-2.0'
导入 cv2
导入 numpy 作为 np
从 PIL 导入 ImageGrab, Image, ImageTk
从 pynput.mouse 导入 Controller 作为 MouseController, Button
从 pynput 导入 keyboard
导入 time
导入 系统
导入 tkinter 作为 tk
导入 threading
导入 queue
导入 configparser
DEFAULT_ROI_X1, DEFAULT_ROI_Y1, DEFAULT_ROI_X2, DEFAULT_ROI_Y2 = (960, 437, 1080, 557)
DEFAULT_HEX_GREY = '#485163'
DEFAULT_HEX_WHITE = '#cecece'
DEFAULT_COLOR_TOLERANCE = 15
DEFAULT_MIDDLE_THRESHOLD = 15
DEFAULT_CLICK_COOLDOWN_DURATION = 0.5
DEFAULT_BAR_THICKNESS_PERCENTAGE = 0.15
DEFAULT_WHITE_AREA_WIDTH_INCREASE = 5
DEFAULT_GREY_LINE_MIN_AREA = 10
DEFAULT_PREDICTION_ENABLED = 真
DEFAULT_LOOKAHEAD_FACTOR = 0.01
DEFAULT_EXPONENTIAL_POWER = 1.015
CONFIG_FILE = 'config.ini'

定义 load_config():
    """
    Loads configuration from config.ini. If the file doesn't exist or is invalid,
    it creates a default config.ini.
    """
    config = configparser.ConfigParser()
    如果 not config.read(CONFIG_FILE):
        打印(f"'{CONFIG_FILE}' not found or could not be read. Creating with default values.")
        config['Detection'] = {'ROI_X1': 字符串(DEFAULT_ROI_X1), 'ROI_Y1': 字符串(DEFAULT_ROI_Y1), 'ROI_X2': 字符串(DEFAULT_ROI_X2), 'ROI_Y2': 字符串(DEFAULT_ROI_Y2), 'HEX_GREY': DEFAULT_HEX_GREY, 'HEX_WHITE': DEFAULT_HEX_WHITE, 'COLOR_TOLERANCE': 字符串(DEFAULT_COLOR_TOLERANCE), 'MIDDLE_THRESHOLD': 字符串(DEFAULT_MIDDLE_THRESHOLD), 'BAR_THICKNESS_PERCENTAGE': 字符串(DEFAULT_BAR_THICKNESS_PERCENTAGE), 'WHITE_AREA_WIDTH_INCREASE': 字符串(DEFAULT_WHITE_AREA_WIDTH_INCREASE), 'GREY_LINE_MIN_AREA': 字符串(DEFAULT_GREY_LINE_MIN_AREA)}
        config['Automation'] = {'CLICK_COOLDOWN_DURATION': 字符串(DEFAULT_CLICK_COOLDOWN_DURATION), 'PREDICTION_ENABLED': 字符串(DEFAULT_PREDICTION_ENABLED), 'LOOKAHEAD_FACTOR': 字符串(DEFAULT_LOOKAHEAD_FACTOR), 'EXPONENTIAL_POWER': 字符串(DEFAULT_EXPONENTIAL_POWER)}
        伴隨 open(CONFIG_FILE, 'w') 作为 configfile:
            config.write(configfile)
        打印(f"Default '{CONFIG_FILE}' created. Please review and adjust values if needed.")
        config.read(CONFIG_FILE)
    roi_x1 = config.getint('Detection', 'ROI_X1', fallback=DEFAULT_ROI_X1)
    roi_y1 = config.getint('Detection', 'ROI_Y1', fallback=DEFAULT_ROI_Y1)
    roi_x2 = config.getint('Detection', 'ROI_X2', fallback=DEFAULT_ROI_X2)
    roi_y2 = config.getint('Detection', 'ROI_Y2', fallback=DEFAULT_ROI_Y2)
    hex_grey = config.get('Detection', 'HEX_GREY', fallback=DEFAULT_HEX_GREY)
    hex_white = config.get('Detection', 'HEX_WHITE', fallback=DEFAULT_HEX_WHITE)
    color_tolerance = config.getint('Detection', 'COLOR_TOLERANCE', fallback=DEFAULT_COLOR_TOLERANCE)
    middle_threshold = config.getint('Detection', 'MIDDLE_THRESHOLD', fallback=DEFAULT_MIDDLE_THRESHOLD)
    bar_thickness_percentage = config.getfloat('Detection', 'BAR_THICKNESS_PERCENTAGE', fallback=DEFAULT_BAR_THICKNESS_PERCENTAGE)
    white_area_width_increase = config.getint('Detection', 'WHITE_AREA_WIDTH_INCREASE', fallback=DEFAULT_WHITE_AREA_WIDTH_INCREASE)
    grey_line_min_area = config.getint('Detection', 'GREY_LINE_MIN_AREA', fallback=DEFAULT_GREY_LINE_MIN_AREA)
    click_cooldown_duration = config.getfloat('Automation', 'CLICK_COOLDOWN_DURATION', fallback=DEFAULT_CLICK_COOLDOWN_DURATION)
    prediction_enabled = config.getboolean('Automation', 'PREDICTION_ENABLED', fallback=DEFAULT_PREDICTION_ENABLED)
    lookahead_factor = config.getfloat('Automation', 'LOOKAHEAD_FACTOR', fallback=DEFAULT_LOOKAHEAD_FACTOR)
    exponential_power = config.getfloat('Automation', 'EXPONENTIAL_POWER', fallback=DEFAULT_EXPONENTIAL_POWER)
    返回 {'ROI_X1': roi_x1, 'ROI_Y1': roi_y1, 'ROI_X2': roi_x2, 'ROI_Y2': roi_y2, 'HEX_GREY': hex_grey, 'HEX_WHITE': hex_white, 'COLOR_TOLERANCE': color_tolerance, 'MIDDLE_THRESHOLD': middle_threshold, 'CLICK_COOLDOWN_DURATION': click_cooldown_duration, 'BAR_THICKNESS_PERCENTAGE': bar_thickness_percentage, 'WHITE_AREA_WIDTH_INCREASE': white_area_width_increase, 'GREY_LINE_MIN_AREA': grey_line_min_area, 'PREDICTION_ENABLED': prediction_enabled, 'LOOKAHEAD_FACTOR': lookahead_factor, 'EXPONENTIAL_POWER': exponential_power}
settings = load_config()
ROI_X1, ROI_Y1, ROI_X2, ROI_Y2 = (settings['ROI_X1'], settings['ROI_Y1'], settings['ROI_X2'], settings['ROI_Y2'])
HEX_GREY = settings['HEX_GREY']
HEX_WHITE = settings['HEX_WHITE']
COLOR_TOLERANCE = settings['COLOR_TOLERANCE']
MIDDLE_THRESHOLD = settings['MIDDLE_THRESHOLD']
CLICK_COOLDOWN_DURATION = settings['CLICK_COOLDOWN_DURATION']
BAR_THICKNESS_PERCENTAGE = settings['BAR_THICKNESS_PERCENTAGE']
WHITE_AREA_WIDTH_INCREASE = settings['WHITE_AREA_WIDTH_INCREASE']
GREY_LINE_MIN_AREA = settings['GREY_LINE_MIN_AREA']
PREDICTION_ENABLED = settings['PREDICTION_ENABLED']
LOOKAHEAD_FACTOR = settings['LOOKAHEAD_FACTOR']
EXPONENTIAL_POWER = settings['EXPONENTIAL_POWER']
mouse = MouseController()
running = 真
image_queue = queue.Queue(maxsize=1)
mask_queue_grey = queue.Queue(maxsize=1)
mask_queue_white = queue.Queue(maxsize=1)
mask_queue_bar = queue.Queue(maxsize=1)
cooldown_active = 假
cooldown_start_time = 0
last_grey_angle = 空
last_grey_time = 空
current_grey_velocity = 0.0
last_grey_distance = 空
current_distance_velocity = 0.0

定义 hex_to_bgr(hex_color):
    """
    Converts a hexadecimal color string (e.g., "#RRGGBB") to an OpenCV BGR NumPy array.
    """
    hex_color = hex_color.lstrip('#')
    返回 np.array([int(hex_color[4:6], 16), 整数(hex_color[2:4], 16), 整数(hex_color[0:2], 16)])

定义 get_screenshot(x1, y1, x2, y2):
    """
    Captures a screenshot of the specified region.
    Returns a NumPy array in BGR format (suitable for OpenCV).
    """
    尝试:
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        返回 cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    异常 Exception 作为 e:
        返回 空

定义 find_colored_area_bgr(bgr_image, target_bgr, color_tolerance, min_area=50, expand_width=0, limit_mask=None):
    """
    Detects a colored area within a BGR image using a color range around the target BGR.
    Expands the detected area by `expand_width` if specified.
    Can be limited to a specific area using `limit_mask`.
    """
    如果 limit_mask is not 空:
        bgr_image = cv2.bitwise_and(bgr_image, bgr_image, mask=limit_mask)
    lower_bound = np.array([max(0, c - color_tolerance) 取 c 自 target_bgr])
    upper_bound = np.array([min(255, c + color_tolerance) 取 c 自 target_bgr])
    mask = cv2.inRange(bgr_image, lower_bound, upper_bound)
    如果 expand_width > 0:
        kernel = np.ones((expand_width, expand_width), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    如果 not contours:
        返回 (None, 空, mask, 空)
    largest_contour = max(contours, key=cv2.contourArea)
    如果 cv2.contourArea(largest_contour) < min_area:
        返回 (None, 空, mask, 空)
    M = cv2.moments(largest_contour)
    如果 M['m00'] == 0:
        返回 (None, 空, mask, 空)
    cX = 整数(M['m10'] / M['m00'])
    cY = 整数(M['m01'] / M['m00'])
    rect = 空
    如果 len(largest_contour) >= 5:
        rect = cv2.minAreaRect(largest_contour)
    返回 ((cX, cY), largest_contour, mask, rect)

定义 detect_curved_bar(image_bgr, roi_width, roi_height, thickness_percentage):
    """
    Creates a mask for the 1st quadrant of a semi-circle and a corresponding
    contour for visualization. This function will always return a mask and a contour,
    regardless of the image content.
    """
    center_x, center_y = (0, roi_height)
    outer_radius = min(roi_width, roi_height)
    thickness = 整数(outer_radius * thickness_percentage)
    inner_radius = outer_radius - thickness
    如果 inner_radius < 0:
        inner_radius = 0
    mask = np.zeros((roi_height, roi_width), dtype=np.uint8)
    cv2.ellipse(mask, (center_x, center_y), (outer_radius, outer_radius), 0, 270, 360, 255, -1)
    cv2.ellipse(mask, (center_x, center_y), (inner_radius, inner_radius), 0, 270, 360, 0, -1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    如果 contours:
        返回 (contours[0], mask)
    否则:
        返回 (None, mask)

定义 on_press(key):
    """Callback for keyboard listener."""
    共用 running
    尝试:
        如果 key == keyboard.Key.esc:
            打印('Escape pressed, stopping script.')
            running = 假
            返回 假
    异常 AttributeError:
        略过
listener = keyboard.Listener(on_press=on_press)
listener.start()
TARGET_GREY_BGR = hex_to_bgr(HEX_GREY)
TARGET_WHITE_BGR = hex_to_bgr(HEX_WHITE)

定义 processing_loop():
    共用 running, cooldown_active, cooldown_start_time, last_grey_angle, last_grey_time, current_distance_velocity
    打印("Starting detection script. Press 'Esc' to stop.")
    打印(f'Monitoring region: ({ROI_X1},{ROI_Y1}) to ({ROI_X2},{ROI_Y2})')
    打印(f'Target Grey BGR: {TARGET_GREY_BGR}, Target White BGR: {TARGET_WHITE_BGR}')
    frame_count = 0
    last_arc_distance = 空
    roi_height = ROI_Y2 - ROI_Y1
    arc_center = (0, roi_height)
    当 running:
        尝试:
            frame_count += 1
            如果 cooldown_active:
                如果 time.time() - cooldown_start_time >= CLICK_COOLDOWN_DURATION:
                    cooldown_active = 假
            screenshot_bgr = get_screenshot(ROI_X1, ROI_Y1, ROI_X2, ROI_Y2)
            如果 screenshot_bgr is 空:
                time.sleep(0.001)
                继续
            display_image_bgr = screenshot_bgr.copy()
            bar_contour, bar_mask = detect_curved_bar(screenshot_bgr, ROI_X2 - ROI_X1, roi_height, BAR_THICKNESS_PERCENTAGE)
            如果 bar_contour is not 空:
                cv2.drawContours(display_image_bgr, [bar_contour], -1, (0, 0, 255), 2)
            white_center, white_contour, white_mask, _ = find_colored_area_bgr(screenshot_bgr, TARGET_WHITE_BGR, COLOR_TOLERANCE, expand_width=WHITE_AREA_WIDTH_INCREASE, limit_mask=bar_mask)
            如果 white_center:
                cv2.circle(display_image_bgr, white_center, 7, (0, 255, 0), -1)
                cv2.drawContours(display_image_bgr, [white_contour], -1, (0, 255, 0), 2)
            grey_center, grey_contour, grey_mask, _ = find_colored_area_bgr(screenshot_bgr, TARGET_GREY_BGR, COLOR_TOLERANCE, min_area=GREY_LINE_MIN_AREA, limit_mask=bar_mask)
            trigger_distance = float('inf')
            current_arc_velocity = 0.0
            如果 grey_center 和 white_center:
                dx_grey = grey_center[0] - arc_center[0]
                dy_grey = grey_center[1] - arc_center[1]
                angle_grey_rad = np.arctan2(dy_grey, dx_grey)
                dx_white = white_center[0] - arc_center[0]
                dy_white = white_center[1] - arc_center[1]
                angle_white_rad = np.arctan2(dy_white, dx_white)
                angle_grey_deg = np.degrees(angle_grey_rad)
                angle_white_deg = np.degrees(angle_white_rad)
                angle_grey_deg_norm = (angle_grey_deg + 360) % 360
                angle_white_deg_norm = (angle_white_deg + 360) % 360
                radius = np.sqrt(dx_grey ** 2 + dy_grey ** 2)
                arc_distance = abs(angle_grey_rad - angle_white_rad) * radius
                如果 last_arc_distance is not 空 和 last_grey_time is not 空:
                    time_diff = time.time() - last_grey_time
                    如果 time_diff > 0:
                        distance_diff = arc_distance - last_arc_distance
                        current_arc_velocity = distance_diff / time_diff
                last_arc_distance = arc_distance
                last_grey_time = time.time()
                如果 PREDICTION_ENABLED:
                    prediction_offset = LOOKAHEAD_FACTOR * pow(abs(current_arc_velocity), EXPONENTIAL_POWER)
                    如果 current_arc_velocity < 0:
                        trigger_distance = arc_distance - prediction_offset
                    否则:
                        trigger_distance = arc_distance
                否则:
                    trigger_distance = arc_distance
                cv2.circle(display_image_bgr, grey_center, 5, (255, 0, 0), -1)
                cv2.drawContours(display_image_bgr, [grey_contour], -1, (255, 0, 0), 2)
                grey_line_end = (int(arc_center[0] + radius * np.cos(angle_grey_rad)), 整数(arc_center[1] + radius * np.sin(angle_grey_rad)))
                cv2.line(display_image_bgr, arc_center, grey_line_end, (255, 0, 0), 1)
                white_line_end = (int(arc_center[0] + radius * np.cos(angle_white_rad)), 整数(arc_center[1] + radius * np.sin(angle_white_rad)))
                cv2.line(display_image_bgr, arc_center, white_line_end, (0, 255, 0), 1)
                start_angle = min(angle_grey_deg_norm, angle_white_deg_norm)
                end_angle = max(angle_grey_deg_norm, angle_white_deg_norm)
                cv2.ellipse(display_image_bgr, arc_center, (int(radius), 整数(radius)), 0, start_angle, end_angle, (255, 255, 255), 2)
            否则:
                current_arc_velocity = 0.0
                last_arc_distance = 空
                last_grey_time = 空
            cv2.putText(display_image_bgr, f'Arc Vel: {current_arc_velocity:.1f} pix/s', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
            cv2.putText(display_image_bgr, f'Trigger Dist: {trigger_distance:.1f}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
            如果 trigger_distance < MIDDLE_THRESHOLD 和 (not cooldown_active):
                打印(f'[{frame_count}] Predicted position is in the middle! Releasing mouse.')
                mouse.release(Button.left)
                cooldown_active = 真
                cooldown_start_time = time.time()
            尝试:
                image_queue.put_nowait(display_image_bgr)
                mask_queue_grey.put_nowait(grey_mask)
                mask_queue_white.put_nowait(white_mask)
                如果 bar_mask is not 空:
                    mask_queue_bar.put_nowait(bar_mask)
            异常 queue.Full:
                略过
            time.sleep(0.01)
        异常 Exception 作为 e:
            打印(f'Exception in processing_loop: {e}', file=sys.stderr)
            time.sleep(1)
    打印('Processing thread stopped.')
root = tk.Tk()
root.title('Detected Elements (Live)')
root.attributes('-topmost', 真)
main_window_width = ROI_X2 - ROI_X1
main_window_height = ROI_Y2 - ROI_Y1
root.geometry(f'{main_window_width}x{main_window_height}')
root.resizable(False, 假)
label_main = tk.Label(root)
label_main.pack()
grey_mask_window = tk.Toplevel(root)
grey_mask_window.title('Grey Line Mask')
grey_mask_window.attributes('-topmost', 真)
label_grey_mask = tk.Label(grey_mask_window)
label_grey_mask.pack()
white_mask_window = tk.Toplevel(root)
white_mask_window.title('White Area Mask')
white_mask_window.attributes('-topmost', 真)
label_white_mask = tk.Label(white_mask_window)
label_white_mask.pack()
bar_mask_window = tk.Toplevel(root)
bar_mask_window.title('Curved Bar Mask (Dark Area)')
bar_mask_window.attributes('-topmost', 真)
label_bar_mask = tk.Label(bar_mask_window)
label_bar_mask.pack()

定义 update_tkinter_image(label, cv_image, tk_window):
    """Helper to convert OpenCV image to PhotoImage and update label."""
    image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    target_width = ROI_X2 - ROI_X1
    target_height = ROI_Y2 - ROI_Y1
    如果 pil_image.width != target_width 或 pil_image.height != target_height:
        pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    new_tk_image = ImageTk.PhotoImage(image=pil_image)
    label.config(image=new_tk_image)
    label.image = new_tk_image
    tk_window.lift()

定义 update_gui_from_queue():
    """Fetches images from queues and updates Tkinter labels."""
    尝试:
        display_image_bgr = image_queue.get_nowait()
        update_tkinter_image(label_main, display_image_bgr, root)
    异常 queue.Empty:
        略过
    尝试:
        grey_mask = mask_queue_grey.get_nowait()
        update_tkinter_image(label_grey_mask, cv2.cvtColor(grey_mask, cv2.COLOR_GRAY2BGR), grey_mask_window)
    异常 queue.Empty:
        略过
    尝试:
        white_mask = mask_queue_white.get_nowait()
        update_tkinter_image(label_white_mask, cv2.cvtColor(white_mask, cv2.COLOR_GRAY2BGR), white_mask_window)
    异常 queue.Empty:
        略过
    尝试:
        bar_mask = mask_queue_bar.get_nowait()
        update_tkinter_image(label_bar_mask, cv2.cvtColor(bar_mask, cv2.COLOR_GRAY2BGR), bar_mask_window)
    异常 queue.Empty:
        略过
    root.after(10, update_gui_from_queue)
processing_thread = threading.Thread(target=processing_loop)
processing_thread.daemon = 真
processing_thread.start()

定义 set_initial_window_positions():
    root.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    window_width = ROI_X2 - ROI_X1
    window_height = ROI_Y2 - ROI_Y1
    grey_mask_window.geometry(f'{window_width}x{window_height}+{root_x + window_width + 10}+{root_y}')
    white_mask_window.geometry(f'{window_width}x{window_height}+{root_x + 2 * window_width + 20}+{root_y}')
    bar_mask_window.geometry(f'{window_width}x{window_height}+{root_x + 3 * window_width + 30}+{root_y}')
    grey_mask_window.resizable(False, 假)
    white_mask_window.resizable(False, 假)
    bar_mask_window.resizable(False, 假)
root.after(100, set_initial_window_positions)
root.after(10, update_gui_from_queue)
尝试:
    root.mainloop()
异常 Exception 作为 e:
    打印(f'Tkinter mainloop error: {e}', file=sys.stderr)
最后:
    running = 假
    listener.stop()
    如果 processing_thread.is_alive():
        processing_thread.join(timeout=1.0)
    如果 'grey_mask_window' 自 locals() 和 grey_mask_window.winfo_exists():
        grey_mask_window.destroy()
    如果 'white_mask_window' 自 locals() 和 white_mask_window.winfo_exists():
        white_mask_window.destroy()
    如果 'bar_mask_window' 自 locals() 和 bar_mask_window.winfo_exists():
        bar_mask_window.destroy()
    如果 'root' 自 locals() 和 root.winfo_exists():
        root.destroy()
    打印('Script finished.')