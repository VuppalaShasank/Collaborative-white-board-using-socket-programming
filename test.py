import os
import socket
import threading
from tkinter import *
from tkinter.colorchooser import askcolor
from tkinter import ttk, filedialog
from PIL import Image, ImageDraw, ImageTk
import base64
from io import BytesIO
import logging

logging.basicConfig(level=logging.DEBUG)

HOST = "192.168.144.227"  # Server IP address
PORT = 5555
BUFFER_SIZE = 1024

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

root = Tk()
root.title("Collaborative Whiteboard")
root.geometry("1050x570+150+50")
root.config(bg="#f2f3f5")
root.resizable(False, False)

current_x, current_y = 0, 0
color = "black"
eraser_on = False

def locate_xy(event):
    global current_x, current_y
    current_x, current_y = event.x, event.y

def add_line(event):
    global current_x, current_y, eraser_on, color
    line_color = "white" if eraser_on else color
    print(f"Adding line from ({current_x}, {current_y}) to ({event.x}, {event.y})")
    if current_x != event.x or current_y != event.y:
        send_data(f"DRAW {current_x} {current_y} {event.x} {event.y} {line_color}")
    canvas.create_line((current_x, current_y, event.x, event.y), width=get_current_value(), fill=line_color, capstyle=ROUND, smooth=True)
    current_x, current_y = event.x, event.y

def toggle_eraser():
    global eraser_on
    eraser_on = not eraser_on

def show_color(new_color):
    global color, eraser_on
    eraser_on = False
    color = new_color

def send_data(data):
    try:
        message = data.encode()
        message_length = len(message)
        client_socket.sendall(message_length.to_bytes(4, 'big'))
        client_socket.sendall(message)
    except Exception as e:
        print(f"Error sending data: {e}")

def insert_image():
    filename = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select Image File", filetypes=(("PNG file", ".png"), ("JPEG file", ".jpg"), ("All files", ".")))
    if filename:
        img = Image.open(filename)
        img.thumbnail((400, 400))  # Resize for display
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_data = base64.b64encode(buffer.getvalue()).decode()
        send_data(f"IMAGE {img_data}")
        photo_img = ImageTk.PhotoImage(img)
        canvas.image = photo_img
        canvas.create_image(200, 100, image=photo_img)

def export_with_logo():
    filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=(("PNG file", ".png"), ("All files", ".*")))
    if filename:
        try:
            # Save canvas as EPS (Encapsulated PostScript)
            canvas.postscript(file="temp_canvas.eps", colormode='color')
            
            # Open the EPS file with Pillow
            with Image.open("temp_canvas.eps") as img:
                img = img.convert("RGBA")  # Ensure proper conversion to PNG-compatible format
                
                # Add the logo
                logo = Image.open("logo.png")
                logo.thumbnail((100, 100))  # Resize the logo
                img.paste(logo, (img.width - 110, img.height - 110), logo)

                # Save the final image
                img.save(filename)

            print(f"Exported image saved as {filename}")

        except Exception as e:
            print(f"Error during export: {e}")

        finally:
            # Ensure the temporary EPS file is removed
            if os.path.exists("temp_canvas.eps"):
                try:
                    os.remove("temp_canvas.eps")
                except Exception as e:
                    print(f"Could not delete temp file: {e}")

eraser_icon = PhotoImage(file="eraser1.png")
eraser_button = Button(root, image=eraser_icon, bg="#f2f3f5", command=toggle_eraser)
eraser_button.place(x=30, y=380)

add_image_icon = PhotoImage(file="addimage.png")
add_image_button = Button(root, image=add_image_icon, bg="#f2f3f5", command=insert_image)
add_image_button.place(x=30, y=430)

export_icon = PhotoImage(file="C:\\Users\\vidya\Desktop\\SH CN\\export.png")
export_button = Button(root, image=export_icon, bg="#f2f3f5", command=export_with_logo)
export_button.place(x=30, y=480)

colors = Canvas(root, bg="#fff", width=37, height=310, bd=0)
colors.place(x=30, y=60)

def display_palette():
    palette = [
        ("black", 10), ("white", 40), ("red", 70), ("orange", 100), 
        ("yellow", 130), ("green", 160), ("blue", 190), ("purple", 220), 
        ("gray", 250), ("brown4", 280)
    ]
    for color_name, y_position in palette:
        id = colors.create_rectangle((10, y_position, 30, y_position + 20), fill=color_name)
        colors.tag_bind(id, '<Button-1>', lambda event, col=color_name: show_color(col))

display_palette()

canvas = Canvas(root, width=870, height=500, background="white", cursor="circle")
canvas.place(x=100, y=10)
canvas.bind('<Button-1>', locate_xy)
canvas.bind('<B1-Motion>', add_line)

current_value = DoubleVar()

def get_current_value():
    return '{: .0f}'.format(current_value.get())

def slider_changed(event):
    value_label.configure(text=get_current_value())
    send_data(f"SLIDER {get_current_value()}")

slider = ttk.Scale(root, from_=0, to=50, orient="vertical", command=slider_changed, variable=current_value, length="200")
slider.place(x=1000, y=130)

value_label = ttk.Label(root, text=get_current_value())
value_label.place(x=1003, y=100)

def receive_data():
    while True:
        try:
            message_length = int.from_bytes(client_socket.recv(4), 'big')
            if not message_length:
                continue
            data = client_socket.recv(message_length).decode()
            logging.debug(f"Data received: {data}")
            handle_server_data(data)
        except Exception as e:
            logging.error(f"Error receiving data: {e}")
            break

def handle_server_data(data):
    print(f"Data received: {data}")  # Debug print
    commands = data.split("\n")
    for command in commands:
        parts = command.split()
        if len(parts) == 6 and parts[0] == "DRAW":
            _, x1, y1, x2, y2, color = parts
            print(f"Drawing line from ({x1}, {y1}) to ({x2}, {y2}) with color {color}")  # Debug print
            canvas.create_line(int(x1), int(y1), int(x2), int(y2), fill=color, capstyle=ROUND, smooth=True)
        elif len(parts) == 5 and parts[0] == "ERASE":
            _, x1, y1, x2, y2, color = parts
            print(f"Erasing line from ({x1}, {y1}) to ({x2}, {y2}) with color {color}")  # Debug print
            canvas.create_line(int(x1), int(y1), int(x2), int(y2), fill=color, capstyle=ROUND, smooth=True)
        elif len(parts) == 4:
            cmd, x, y, color = parts
            if cmd == "DRAW":
                canvas.create_line(int(x), int[y], int(x) + 1, int[y] + 1, fill=color)
        elif len(parts) == 2:
            cmd, img_data = parts
            if cmd == "IMAGE":
                img = Image.open(BytesIO(base64.b64decode(img_data)))
                photo_img = ImageTk.PhotoImage(img)
                canvas.image = photo_img
                canvas.create_image(200, 100, image=photo_img)
        elif len(parts) == 2 and parts[0] == "SLIDER":
            _, value = parts
            current_value.set(float(value))
            value_label.configure(text=value)

threading.Thread(target=receive_data, daemon=True).start()

root.mainloop()