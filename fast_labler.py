import cv2
import os
import numpy as np
import json

# %% HELPERS


def __mouse_callback(event, x, y, flags, params):
    global rectangle, rect, ix, iy, m_state

    if event == cv2.EVENT_RBUTTONDOWN:
        cv2.destroyAllWindows()

    if event == cv2.EVENT_MBUTTONDOWN:
        # switches between xi, yi midpoint and rectangle edge
        print('Switched selection mode!')
        m_state = not m_state

    if event == cv2.EVENT_LBUTTONDOWN:
        rectangle = True
        ix, iy = x, y

    if event == cv2.EVENT_MOUSEMOVE and rectangle:
        if m_state:
            w = 2 * abs(ix-x)
            h = 2 * abs(iy-y)
            rect = [int(ix-w/2), int(iy-h/2), int(w), int(h)]
        else:
            w = abs(ix-x)
            h = abs(iy-y)
            rect = [min(ix, x), min(iy, y), abs(ix-x), abs(iy-y)]

    if event == cv2.EVENT_LBUTTONUP:
        rectangle = False
        if m_state:
            w = 2 * abs(ix-x)
            h = 2 * abs(iy-y)
            rect = [int(ix-w/2), int(iy-h/2), int(w), int(h)]
        else:
            w = abs(ix-x)
            h = abs(iy-y)
            rect = [min(ix, x), min(iy, y), abs(ix-x), abs(iy-y)]


def __processBackground(img_background, coordinates, alpha, rect_null, edit_selector, scale):
    for idx, coordinate in enumerate(coordinates):
        rect_loc = coordinate[:4]
        if rect_loc != rect_null:
            label_loc = coordinate[-1]
            if idx == edit_selector:
                col = (0, 0, 255)
                alpha_cur = 0
            else:
                col = (0, 255, 0)
                alpha_cur = alpha
            old_background = np.zeros_like(img_background, np.uint8)
            cv2.rectangle(old_background, (rect_loc[0], rect_loc[1]), (
                rect_loc[0]+rect_loc[2], rect_loc[1]+rect_loc[3]), col, 2)
            cv2.rectangle(old_background, (rect_loc[0]-1, rect_loc[1]),
                          (rect_loc[0]+int(30*scale), rect_loc[1]-int(38*scale)), col, thickness=-1)
            mask = old_background.astype(bool)
            img_background[mask] = cv2.addWeighted(
                img_background, alpha_cur, old_background, 1 - alpha_cur, 0)[mask]
            cv2.putText(img_background, str(
                label_loc), (rect_loc[0], rect_loc[1]-3), cv2.FONT_HERSHEY_SIMPLEX, 1.3*scale, col, 2)


def __processSelection(img, rect_loc, label_loc, rect_null, scale):
    if rect_loc != rect_null:
        cv2.rectangle(img, (rect_loc[0], rect_loc[1]), (rect_loc[0] +
                      rect_loc[2], rect_loc[1]+rect_loc[3]), (0, 255, 0), 2)
        cv2.rectangle(img, (rect_loc[0]-1, rect_loc[1]),
                      (rect_loc[0]+int(30*scale), rect_loc[1]-int(38*scale)), (0, 255, 0), thickness=-1)
        cv2.putText(img, str(
            label_loc), (rect_loc[0], rect_loc[1]-3), cv2.FONT_HERSHEY_SIMPLEX, 1.3*scale, (255, 255, 255), 2)


def __processRect(rect_loc, label_selector, bounds, bound_selection, rect_null):
    if rect_loc == rect_null:
        return [*rect_null, -1]
    if bound_selection:
        for dim, limit in enumerate(bounds):
            # low edges
            if rect_loc[dim] < 0:
                rect_loc[dim+2] = rect_loc[dim+2] + rect_loc[dim]
                rect_loc[dim] = 0
            # high edges
            if rect_loc[dim] + rect_loc[dim+2] >= limit:
                rect_loc[dim+2] = limit - 1 - rect[dim]
    return [*rect_loc, label_selector]


def exportJson(DIR, data):
    for key, value in data.items():
        annotation = {}
        annotation['image'] = key
        annotation['bboxes'] = value
        # saves the json file at the specified location with the corresponding name of the image
        with open(os.path.join(DIR, f'{os.path.basename(key).split(".")[0]}.json'), 'w') as p:
            json.dump(annotation, p)

# %% main


def FastLabler(path_images, data={}, bound_selection=True, save_dict=True, save_json=False, path_annotations=None, rect_null=[-1, -1, -1, -1], show_legend=True, alpha=0.8):
    if not path_annotations:
        path_annotations = path_images

    files = []
    for img_name in os.listdir(path_images):
        if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(path_images, img_name)
            files.append(img_path)

    quit = False
    label_selector = 0
    iFrame = 0
    global rectangle, rect, ix, iy, m_state
    m_state = False
    while True:
        img_path = files[iFrame]
        rectangle = False
        rect = rect_null

        img = cv2.imread(img_path)  # current picture
        img_orig = cv2.imread(img_path)  # original picture
        img_legend = cv2.imread(img_path)  # original with legend
        bounds = img.shape[1::-1]
        scale = bounds[1]/720
        for idx, (letter, description) in enumerate([("L", "Toggle Legend"), ("A", "Add New Label"), ("Z", "Previous Frame"), ("X", "Next Frame"), ("Rclick", "Add Lebel and Next Frame/Null Annotation"), ("Lclick", "Selection"), ("Mclick", "Toggle Selection Mode"), ("0-9", "Change Label"), ("E", "Edit Mode"), ("D", "Delete Annotation"), ("S", "Save and Quit"), ("Q", "Cancel")]):
            cv2.putText(img_legend, letter, (0, idx * int(24*scale) + int(24*scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7*scale, (255, 255, 255), 1)
            cv2.putText(img_legend, description, (int(120*scale), idx * int(24*scale) + int(24*scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7*scale, (255, 255, 255), 1)
        if show_legend:
            img = img_legend.copy()
            img_background = img_legend.copy()
        else:
            img_background = img_orig.copy()

        # restore information
        if img_path in data:
            coordinates = data[img_path]
            __processBackground(img_background, coordinates,
                                alpha, rect_null, -1, scale)
        else:
            coordinates = []

        cv2.namedWindow(img_path)
        cv2.setMouseCallback(img_path, __mouse_callback)
        img = img_background.copy()
        cv2.imshow(img_path, img)

        key = -1
        edit_mode = False
        edit_selector = -1
        while True:
            key = cv2.waitKey(15)
            if key != -1:
                key = ord(chr(key).lower()) # to lowercase
            update_background = False
            update_selection = False
            if not cv2.getWindowProperty(img_path, cv2.WND_PROP_VISIBLE):
                edit_mode = False
                # only add rect_null if coordinates is empty
                if len(coordinates) == 0 or rect != rect_null:
                    print(__processRect(rect, label_selector,
                          bounds, bound_selection, rect_null))
                    coordinates.append(__processRect(
                        rect, label_selector, bounds, bound_selection, rect_null))
                    rect = rect_null
                iFrame = (iFrame + 1) % len(files)
                break
            if key == ord('e'):
                edit_mode = not edit_mode
                # only enter edit mode when there is something to edit
                if edit_mode and len(coordinates) == 0:
                    edit_mode = False
                if edit_mode:
                    edit_selector = len(coordinates) - 1
                    update_background = True
                else:
                    edit_selector = -1
                    update_background = True
            if key == ord('z'):
                if edit_mode:
                    edit_selector = (edit_selector - 1) % len(coordinates)
                    update_background = True
                else:
                    cv2.destroyWindow(img_path)
                    iFrame = (iFrame - 1) % len(files)
                    break
            if key == ord('x'):
                if edit_mode:
                    edit_selector = (edit_selector + 1) % len(coordinates)
                    update_background = True
                else:
                    cv2.destroyWindow(img_path)
                    iFrame = (iFrame + 1) % len(files)
                    break
            if key == ord('d') and edit_mode:
                coordinates.pop(edit_selector)
                update_background = True
                if len(coordinates) == 0:
                    edit_selector = -1
                    edit_mode = False
                else:
                    edit_selector = (edit_selector) % len(coordinates)
            if key == ord('s'):
                save_data = True
                quit = True
                break
            if key == ord('q'):
                save_data = False
                quit = True
                break
            if key >= 48 and key <= 57:
                update_selection = True
                label_selector = key - 48
                if edit_mode:
                    coordinates[edit_selector][-1] = label_selector
                    update_background = True
            if rectangle:
                update_selection = True
                img[:] = img_background[:]  # remove previous selection
            if key == ord('a') and not edit_mode:
                update_background = True  # remove selection
                if len(coordinates) == 0 or rect != rect_null:
                    print(__processRect(rect, label_selector, bounds, bound_selection, rect_null))
                    coordinates.append(__processRect(rect, label_selector, bounds, bound_selection, rect_null))
                    rect = rect_null

            if key == ord('l'):
                show_legend = not show_legend
                update_background = True

            # reset background and add annotations back
            if update_background:
                if show_legend:
                    img_background = img_legend.copy()
                else:
                    img_background = img_orig.copy()
                __processBackground(img_background, coordinates,
                                    alpha, rect_null, edit_selector, scale)
                img = img_background.copy()

            # add selection if not in edit mode
            if (not edit_mode and key != ord('a')) and (update_selection or update_background):
                __processSelection(img, rect, label_selector, rect_null, scale)

            if update_background or update_selection:
                cv2.imshow(img_path, img)

        if quit:
            break

        # remove rect_null if it is not the only annotation
        if len(coordinates) >= 2:
            coordinates = [s for s in coordinates if s[:4] != rect_null]

        # update dictionary before closing picture in case coordinates is not empty
        if len(coordinates):
            data[img_path] = coordinates

    cv2.destroyAllWindows()

    if save_data and save_dict:
        np.save(os.path.join(path_annotations, "data.npy"), data)

    if save_data and save_json:
        exportJson(path_annotations, data)

    return data
