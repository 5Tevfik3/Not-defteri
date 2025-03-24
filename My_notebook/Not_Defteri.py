import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, scrolledtext, colorchooser
from datetime import datetime
from tkcalendar import DateEntry
import json

# Veritabanı bağlantısı
conn = sqlite3.connect("notes.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note TEXT NOT NULL,
    date TEXT NOT NULL,
    category TEXT NOT NULL
)
""")
conn.commit()

# Ayarları json kullanarak yükleme ve kaydetme
def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"theme": "Klasik", "font": "Arial", "size": 12, "color": "black"}

def save_settings(settings):
    with open("settings.json", "w") as f:
        json.dump(settings, f)

# Tema ve yazı ayarları uygulama
def apply_settings(settings):
    global current_bg_color, current_font_color, current_font
    themes = {
        "Klasik": ("white", "black", "lightgray"),
        "Koyu": ("gray15", "white", "darkgray"),
        "Mavi": ("lightblue", "black", "skyblue")
    }
    if settings["theme"] in themes:
        bg_color, font_color, button_color = themes[settings["theme"]]
        top.config(bg=bg_color)
        note_entry.config(fg=settings["color"], font=(settings["font"], settings["size"]))
        search_entry.config( fg=settings["color"])  

        # notes_list için stil güncellemesi
        style = ttk.Style()
        style.configure("Treeview", background=bg_color, 
                        fieldbackground=bg_color,  # Hücrelerin arka plan rengi
                        foreground=settings["color"], 
                        font=(settings["font"], settings["size"]))
        notes_list.configure(style="Treeview")

    current_font = (settings["font"], settings["size"])
    current_font_color = settings["color"]
    current_bg_color = bg_color

settings_window = None  # Global değişken ile pencereyi takip edelim

def open_settings():   #Ayarlar penceresi
    global settings_window
    if settings_window is not None and settings_window.winfo_exists():
        settings_window.focus()  # Eğer açıksa, sadece pencereye odaklan
        return

    settings_window = tk.Toplevel(top)
    settings_window.title("Ayarlar")
    settings = load_settings()

    options = [
        ("Tema Seçin:", ["Klasik", "Koyu", "Mavi"], "theme"),
        ("Yazı Tipi Seçin:", ["Arial", "Courier", "Helvetica", "Times New Roman"], "font"),
        ("Yazı Boyutu Seçin:", [10, 12, 14, 16, 18, 20], "size"),
        ("Yazı Rengi Seçin:", ["Black", "Red", "Green", "Blue", "White"], "color")
    ]

    settings_values = {}
    for row, (label, values, key) in enumerate(options):
        tk.Label(settings_window, text=label).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        combobox = ttk.Combobox(settings_window, values=values, state="readonly")
        combobox.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        combobox.set(settings[key])
        settings_values[key] = combobox

    settings_window.protocol("WM_DELETE_WINDOW", lambda: close_settings_window()) # pencere kapatıldığında global değişkeni güncelle

    def choose_color():
        color = colorchooser.askcolor()[1]
        if color:
            settings_values["color"].set(color)
            settings["color"] = color  # Ayarları güncelle
    
    tk.Button(settings_window, text="Renk Seç", command=choose_color).grid(row=4, column=2, padx=10, pady=5)

    def apply_and_save():
        for key, combobox in settings_values.items():
            settings[key] = combobox.get()
        save_settings(settings)
        apply_settings(settings)
        close_settings_window() # Ayarları uyguladıktan sonra pencereyi kapat

    tk.Button(settings_window, text="Uygula", command=apply_and_save).grid(row=len(options), column=0, columnspan=2, pady=10)

def close_settings_window():
    global settings_window
    if settings_window is not None:
        settings_window.destroy()
        settings_window = None

def save_note(): #Not kaydetme
    note_text = note_entry.get("1.0", tk.END).strip()
    selected_date_str = date_entry.get().replace(".", "/")  # Noktaları eğik çizgiye çevir
    
    try:
        selected_date = datetime.strptime(selected_date_str, "%d/%m/%Y").date()
    except ValueError:
        messagebox.showerror("Tarih Hatası", f"Tarih formatı hatalı: {selected_date_str}")
        return

    current_date = datetime.today().date()

    if selected_date < current_date:
        messagebox.showwarning("Uyarı", "Bugün veya gelecekteki tarihlerde not ekleyebilirsiniz!")
        return

    selected_category = category_var.get()

    if note_text and selected_category:
        try:
            cursor.execute("INSERT INTO notes (note, date, category) VALUES (?, ?, ?)", 
                           (note_text, selected_date_str, selected_category))
            conn.commit()
            note_entry.delete("1.0", tk.END)
            load_notes()
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Not kaydedilirken bir hata oluştu: {e}")
    else:
        messagebox.showwarning("Uyarı", "Lütfen bir not ve kategori girin!")

def load_notes(search_query=""):  #Notları yükleme
    notes_list.delete(*notes_list.get_children())
    try:
        if search_query:
            cursor.execute("SELECT id, note, date, category FROM notes WHERE note LIKE ? ORDER BY date DESC", ('%' + search_query + '%',))
        else:
            cursor.execute("SELECT id, note, date, category FROM notes ORDER BY date DESC")
        for row in cursor.fetchall():
            notes_list.insert("", "end", values=row)
    except sqlite3.Error as e:
        messagebox.showerror("Veritabanı Hatası", f"Notlar yüklenirken bir hata oluştu: {e}")

def delete_note(event=None): #Notları silme
    selected_item = notes_list.selection()
    if selected_item:
        note_id = notes_list.item(selected_item, "values")[0]
        try:
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            load_notes()
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Not silinirken bir hata oluştu: {e}")
    else:
        messagebox.showwarning("Uyarı", "Lütfen bir not seçin!")

def update_note(event=None): #Notları güncelleme
    selected_item = notes_list.selection()
    if selected_item:
        note_id, note_text, note_date, note_category = notes_list.item(selected_item, "values")
        note_entry.delete("1.0", tk.END)
        note_entry.insert("1.0", note_text)
        date_entry.set_date(note_date)
        category_var.set(note_category)

        def save_update():
            new_note_text = note_entry.get("1.0", tk.END).strip()
            new_date = date_entry.get()
            new_category = category_var.get()

            if new_note_text and new_category:
                try:
                    cursor.execute("UPDATE notes SET note = ?, date = ?, category = ? WHERE id = ?", (new_note_text, new_date, new_category, note_id))
                    conn.commit()
                    note_entry.delete("1.0", tk.END)
                    load_notes()
                    save_update_btn.destroy()  # Butonu yok ediyoruz.
                except sqlite3.Error as e:
                    messagebox.showerror("Veritabanı Hatası", f"Not güncellenirken bir hata oluştu: {e}")
            else:
                messagebox.showwarning("Uyarı", "Not ve kategori boş olamaz!")

        global save_update_btn
        if 'save_update_btn' in globals():
            save_update_btn.destroy()

        save_update_btn = tk.Button(top, text="Değişiklikleri Kaydet", command=save_update)
        save_update_btn.pack()

def search_notes():   #Not arama
    search_text = search_entry.get()
    load_notes(search_text)

def search_notes_enter(event):
    search_notes()

# Global değişken ile pencereyi takip edelim
details_window = None

def show_note_details(event):  #Not detaylarını gösterme
    global details_window
    if details_window is not None and details_window.winfo_exists():
        return
    selected_item = notes_list.selection()
    if selected_item:
        note_id, note_text, note_date, note_category = notes_list.item(selected_item, "values")

        details_window = Toplevel(top)
        details_window.title("Not Detayları")
        details_window.geometry("500x400") # Pencere Boyutu

        tk.Label(details_window, text="Not İçeriği:", font=("Arial", 12, "bold")).pack(pady=5)
        details_text = scrolledtext.ScrolledText(details_window, wrap=tk.WORD, width=60, height=15)
        details_text.insert(tk.END, note_text)
        details_text.config(state=tk.DISABLED)
        details_text.pack(padx=10, pady=10)

        # Tarih ve kategori etiketlerini ekleyelim
        tk.Label(details_window, text=f"Tarih: {note_date}", font=("Arial", 10)).pack()
        tk.Label(details_window, text=f"Kategori: {note_category}", font=("Arial", 10)).pack()

        details_window.protocol("WM_DELETE_WINDOW", lambda: close_details_window())

def close_details_window():
    global details_window
    if details_window is not None:
        details_window.destroy()
        details_window = None

def show_context_menu(event): #Sağ tıklama menüsü
    selected_item = notes_list.identify_row(event.y)
    if selected_item:
        notes_list.selection_set(selected_item)
        context_menu.post(event.x_root, event.y_root)

# Tkinter arayüzü
top = tk.Tk()
top.title("Not Defteri")
top.geometry("840x550")

# Not yazma alanı
tk.Label(top, text="Notunuzu Girin:").pack()
note_entry_frame = tk.Frame(top, width=700, height=140)  # Sabit bir çerçeve oluşturduk
note_entry_frame.pack_propagate(False)  # Çerçevenin genişlemesini engelledik
note_entry_frame.pack()

note_entry = tk.Text(note_entry_frame, wrap=tk.WORD, font=("Arial", 12))  # Varsayılan font boyutu
note_entry.pack(fill=tk.BOTH, expand=True)


# Tarih, Kategori, Kaydet ve Ayarlar butonları için frame
input_frame = tk.Frame(top)
input_frame.pack(pady=10)

# Ayarlar butonu
settings_button = tk.Button(input_frame, text="Ayarlar", command=open_settings)
settings_button.grid(row=0, column=5, padx=5)

# Tarih seçimi
tk.Label(input_frame, text="Tarih Seçin:").grid(row=0, column=0, padx=5)
date_entry = DateEntry(input_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
date_entry.grid(row=0, column=1, padx=10)

# Kategori seçimi
tk.Label(input_frame, text="Kategori:").grid(row=0, column=2, padx=25)
category_var = tk.StringVar()
category_combobox = ttk.Combobox(input_frame, textvariable=category_var, values=["İş", "Kişisel", "Hatırlatma", "Alışveriş", "Diğer"], state="readonly")
category_combobox.grid(row=0, column=3, padx=5)
category_combobox.current(0)

# Kaydet butonu
save_button = tk.Button(input_frame, text="Kaydet", command=save_note)
save_button.grid(row=0, column=4, padx=110)

# Kaydedilen notlar
tk.Label(top, text="Kaydedilen Notlar").pack()

columns = ("ID", "Not", "Tarih", "Kategori")
notes_list = ttk.Treeview(top, columns=columns, show="headings")
for col in columns:
    notes_list.heading(col, text=col)
notes_list.pack(pady=10)

# Sağ tıklama menüsü
context_menu = tk.Menu(top, tearoff=0)# Sağ tıklama menüsü
context_menu.add_command(label="Sil", command=delete_note)# Silme seçeneği
context_menu.add_command(label="Düzenle", command=update_note)#Notları düzenleme seçeneği

# Arama çubuğu
search_frame = tk.Frame(top)
search_frame.pack()

tk.Label(search_frame, text="Notlarda Ara").grid(row=0, column=0)#Notları arama yeri oluşturduk
search_entry = tk.Entry(search_frame)
search_entry.grid(row=0, column=1)

search_button = tk.Button(search_frame, text="Ara", command=search_notes)# "Ara" butonunu giriş alanının yanına imleç şeklinde yerleştiriyoruz.
search_button.grid(row=0, column=2)#Butonu frame'e yerleştiriyoruz.

# Arama çubuğu iyileştirmesi (Enter tuşu)
search_entry.bind("<Return>", search_notes_enter)
notes_list.bind("<Button-3>", show_context_menu)#Kayıt edilen notlara sağ tıklama olayı ekledik
notes_list.bind("<Double-1>", show_note_details)#Not detayları için çiıft tıklama

# Ayarları yükle ve uygula
settings = load_settings()
apply_settings(settings)

load_notes()

top.mainloop()