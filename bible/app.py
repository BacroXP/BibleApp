import customtkinter
import json
import os

class BibleApp:
    def __init__(self):
        self.root = customtkinter.CTk()
        self.root.title("Bible App")
        self.root.geometry("1000x600")

        os.makedirs("comments", exist_ok=True)
        self.current_note_file = None

        # Load JSON data
        self.books_data = self.load_books_json("texts/luther1912.json")
        self.original = self.load_books_json("texts/original.json")

        # Preprocess original for fast lookup
        self.original_lookup = {}
        for b in self.original:
            book_num = b["book"]
            self.original_lookup[book_num] = {}
            for c in b["chapters"]:
                chap_key = c["chapter"]
                self.original_lookup[book_num][chap_key] = {v["verse"]: v["content"] for v in c["verses"]}

        self.init()

    def load_books_json(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def init(self):
        self.init_sidebar()
        self.init_main_frames()
        self.show_welcome()
        self.root.bind("<Configure>", self.on_resize)

    def init_sidebar(self):
        self.sidebar = customtkinter.CTkFrame(self.root, width=200, fg_color="#00149D", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.load_books()

    def init_main_frames(self):
        self.left_frame = customtkinter.CTkFrame(self.root, fg_color="#FFFFFF", corner_radius=0)
        self.left_frame.pack(side="left", fill="both", expand=True)
        self.right_frame = None

    def show_welcome(self):
        label = customtkinter.CTkLabel(
            self.left_frame,
            text="Willkommen zur Lutherbibel 1912!",
            font=customtkinter.CTkFont(size=20, weight="bold"),
            text_color="#4857B4"
        )
        label.pack(pady=20)

    def load_books(self):
        if hasattr(self, "book_list"):
            self.book_list.pack_forget()

        self.book_list = customtkinter.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color="#001CD1", scrollbar_button_hover_color="#334EFF"
        )
        self.book_list.pack(fill="both", expand=True, padx=10, pady=10)

        for book in self.books_data:
            btn = customtkinter.CTkButton(
                self.book_list,
                text=book["name"],
                fg_color="transparent",
                hover_color="#001CD1",
                command=lambda b=book: self.load_chapters(b)
            )
            btn.pack(fill="x", pady=2)

    def load_chapters(self, book):
        self.book_list.pack_forget()

        self.chapters_list = customtkinter.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color="#001CD1", scrollbar_button_hover_color="#334EFF"
        )
        self.chapters_list.pack(fill="both", expand=True, padx=10, pady=10)

        for b in self.books_data:
            if b["name"] == book["name"]:
                for chapter in [{"chapter": "Zurück"}] + b["chapters"]:
                    display_chapter = chapter["chapter"]
                    if book["book"] <= 39 and chapter["chapter"] != "Zurück":
                        display_chapter = self.dec_to_hebrew(int(chapter["chapter"]))
                    btn = customtkinter.CTkButton(
                        self.chapters_list,
                        text=display_chapter,
                        fg_color="transparent",
                        hover_color="#001CD1",
                        command=lambda b=book, c=chapter: self.handle_chapter(b, c)
                    )
                    btn.pack(fill="x", pady=2)
                break

    def handle_chapter(self, book, chapter):
        if chapter["chapter"] == "Zurück":
            if hasattr(self, "verse_display"):
                self.verse_display.pack_forget()
            if hasattr(self, "chapter_frame"):
                self.chapter_frame.pack_forget()
            self.chapters_list.pack_forget()
            self.load_books()
            return

        # --- COMMENT SYSTEM (AUTO FILE) ---
        filename = f"{book['name']}_{chapter['chapter']}.txt".replace(" ", "_")
        self.current_note_file = os.path.join("comments", filename)

        if not os.path.exists(self.current_note_file):
            open(self.current_note_file, "w", encoding="utf-8").close()

        if hasattr(self, "comment_selector"):
            files = self.get_comment_files()
            self.comment_selector.configure(values=files if files else ["Keine Dateien"])
            self.comment_selector.set(filename)
            self.comment_title.configure(text=filename)
            self.select_comment(filename)

        # --- ORIGINAL LEFT SIDE ---
        for widget in self.left_frame.winfo_children():
            widget.destroy()

        title = customtkinter.CTkLabel(
            self.left_frame,
            text=f"{book['name']} - {chapter['chapter']}",
            font=customtkinter.CTkFont(size=20, weight="bold"),
            text_color="#4857B4"
        )
        title.pack(pady=10)

        self.chapter_frame = customtkinter.CTkScrollableFrame(
            self.left_frame, fg_color="transparent",
            scrollbar_button_color="#1B33CC", scrollbar_button_hover_color="#5062D8"
        )
        self.chapter_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.separator = customtkinter.CTkFrame(self.left_frame, height=2, fg_color="#DDDDDD")
        self.separator.pack(fill="x", padx=10, pady=5)

        self.verse_display = customtkinter.CTkFrame(self.left_frame, fg_color="#FFFFFF")
        self.ref_label = customtkinter.CTkLabel(
            self.verse_display, text="", font=customtkinter.CTkFont(weight="bold"), text_color="#4958A1"
        )
        self.ref_label.pack(anchor="w", padx=5, pady=(5,0))
        self.luther_label = customtkinter.CTkLabel(self.verse_display, text="", justify="left", text_color="#555555")
        self.luther_label.pack(anchor="w", padx=5, pady=(2,0))
        self.original_label = customtkinter.CTkLabel(self.verse_display, text="", justify="left", text_color="#555555")
        self.original_label.pack(anchor="w", padx=5, pady=(2,5))
        self.copy_button = customtkinter.CTkButton(self.verse_display, text="Kopieren", command=self.copy_verse)
        self.copy_button.pack(anchor="e", padx=5, pady=5)

        self.current_selected_text = None
        self.current_selected_verse = None

        for verse in chapter["verses"]:
            self.create_verse(book, chapter, verse)

        self.left_frame.bind("<Configure>", lambda e: self.update_wraplengths(book, chapter))

    # -------- RIGHT SIDE -------- #

    def init_comment_section(self):
        # Title container (fix)
        self.title_frame = customtkinter.CTkFrame(self.right_frame, fg_color="transparent")
        self.title_frame.pack(fill="x", pady=(10, 5))

        self.comment_title = customtkinter.CTkLabel(
            self.title_frame,
            text="Kein Kommentar geöffnet",
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color="#4857B4",
            cursor="hand2"
        )
        self.comment_title.pack()
        self.comment_title.bind("<Button-1>", self.enable_rename)

        top_frame = customtkinter.CTkFrame(self.right_frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=10)

        self.comment_selector = customtkinter.CTkOptionMenu(
            top_frame,
            values=self.get_comment_files() or ["Keine Dateien"],
            command=self.select_comment,
            dropdown_fg_color="#2A65BD",
            dropdown_hover_color="#7582D3",
            dropdown_text_color="#FFFFFF"
        )
        self.comment_selector.pack(side="left", fill="x", expand=True, padx=(0,5))

        self.add_button = customtkinter.CTkButton(
            top_frame, text="+", width=40, command=self.add_comment
        )
        self.add_button.pack(side="right", padx=(5,0))

        self.delete_button = customtkinter.CTkButton(
            top_frame, text="Löschen", width=80, command=self.delete_comment
        )
        self.delete_button.pack(side="right")

        self.notes_canvas = customtkinter.CTkCanvas(self.right_frame, bg="#F5F5F5", highlightthickness=0)
        self.notes_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.notes_textbox = customtkinter.CTkTextbox(
            self.notes_canvas, fg_color="transparent", wrap="word",
            font=("Segoe Script", 16), text_color="#333333", border_width=0 
        )

        self.text_window = self.notes_canvas.create_window((0, 0), window=self.notes_textbox, anchor="nw", width=300)

        self.notes_canvas.bind("<Configure>", self.resize_notes_canvas)
        self.notes_textbox.bind("<KeyRelease>", self.save_note)

        self.show_placeholder()

    def get_comment_files(self):
        return [f for f in os.listdir("comments") if f.endswith(".txt")]

    def select_comment(self, choice):
        if choice == "Keine Dateien":
            return
        self.current_note_file = os.path.join("comments", choice)
        self.comment_title.configure(text=choice)
        with open(self.current_note_file, "r", encoding="utf-8") as f:
            text = f.read()
        self.notes_textbox.delete("1.0", "end")
        self.notes_textbox.insert("1.0", text)
    
    def add_comment(self):
        existing = self.get_comment_files()
        i = 1
        while True:
            name = f"Kommentar_{i}.txt"
            if name not in existing:
                break
            i += 1

        path = os.path.join("comments", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("")

        files = self.get_comment_files()
        self.comment_selector.configure(values=files)
        self.comment_selector.set(name)

        self.current_note_file = path
        self.comment_title.configure(text=name)
        self.notes_textbox.delete("1.0", "end")

    def delete_comment(self):
        if not self.current_note_file:
            return
        if os.path.exists(self.current_note_file):
            os.remove(self.current_note_file)
        self.current_note_file = None
        self.comment_title.configure(text="Kein Kommentar geöffnet")
        self.notes_textbox.delete("1.0", "end")
        self.show_placeholder()
        self.comment_selector.configure(values=self.get_comment_files() or ["Keine Dateien"])

    def save_note(self, event=None):
        if not self.current_note_file:
            return
        text = self.notes_textbox.get("1.0", "end").strip()
        with open(self.current_note_file, "w", encoding="utf-8") as f:
            f.write(text)

    def show_placeholder(self):
        self.notes_textbox.delete("1.0", "end")
        self.notes_textbox.insert("1.0", "Wähle ein Kapitel oder öffne einen Kommentar...")
    
    def enable_rename(self, event=None):
        if not self.current_note_file:
            return

        current_name = os.path.basename(self.current_note_file).replace(".txt", "")

        for widget in self.title_frame.winfo_children():
            widget.destroy()

        self.rename_entry = customtkinter.CTkEntry(
            self.title_frame,
            font=customtkinter.CTkFont(size=18),
            fg_color="transparent",
            border_width=0,
            text_color="#4857B4",
        )
        self.rename_entry.insert(0, current_name)
        self.rename_entry.pack()
        self.rename_entry.focus()

        self.rename_entry.bind("<Return>", self.finish_rename)
        self.rename_entry.bind("<FocusOut>", self.finish_rename)
    
    def finish_rename(self, event=None):
        if not hasattr(self, "rename_entry"):
            return

        new_name = self.rename_entry.get().strip()

        for widget in self.title_frame.winfo_children():
            widget.destroy()

        if not new_name:
            new_name = os.path.basename(self.current_note_file).replace(".txt", "")

        new_filename = f"{new_name}.txt"
        new_path = os.path.join("comments", new_filename)

        if os.path.exists(new_path) and new_path != self.current_note_file:
            new_filename = os.path.basename(self.current_note_file)
            new_path = self.current_note_file
        else:
            os.rename(self.current_note_file, new_path)
            self.current_note_file = new_path

        self.comment_title = customtkinter.CTkLabel(
            self.title_frame,
            text=new_filename,
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color="#4857B4",
            cursor="hand2"
        )
        self.comment_title.pack()
        self.comment_title.bind("<Button-1>", self.enable_rename)

        files = self.get_comment_files()
        self.comment_selector.configure(values=files)
        self.comment_selector.set(new_filename)

    def resize_notes_canvas(self, event):
        self.notes_canvas.itemconfig(self.text_window, width=event.width)

    # -------- RESIZE -------- #

    def on_resize(self, event):
        if event.widget == self.root:
            if self.root.winfo_width() >= 900:
                if self.right_frame is None:
                    self.right_frame = customtkinter.CTkFrame(self.root, fg_color="#EEEEEE", corner_radius=0)
                    self.right_frame.pack(side="left", fill="both", expand=True)
                    self.init_comment_section()
            else:
                if self.right_frame:
                    self.right_frame.destroy()
                    self.right_frame = None

    # -------- LEFT SIDE VERSES (UNCHANGED) -------- #

    def create_verse(self, book, chapter, verse):
        frame = customtkinter.CTkFrame(self.chapter_frame, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        frame.grid_columnconfigure(1, weight=1)

        num = customtkinter.CTkLabel(frame, text=verse["verse"], text_color="#3B5BFF", width=35)
        num.grid(row=0, column=0, padx=(5, 10), sticky="nw")
        txt = customtkinter.CTkLabel(frame, text=verse["content"], text_color="#555555", justify="left", anchor="w")
        txt.grid(row=0, column=1, sticky="nsew")

        def click(e=None, b=book, c=chapter, v=verse):
            self.current_selected_verse = v
            self.show_verse(b, c, v)

        frame.bind("<Button-1>", click)
        num.bind("<Button-1>", click)
        txt.bind("<Button-1>", click)

    def update_wraplengths(self, book, chapter):
        max_width = self.left_frame.winfo_width() - 60
        if max_width <= 0:
            max_width = 800

        for child in self.chapter_frame.winfo_children():
            for lbl in child.winfo_children():
                if isinstance(lbl, customtkinter.CTkLabel) and lbl.cget("text") != "":
                    lbl.configure(wraplength=max_width)

        if self.current_selected_verse:
            self.show_verse(book, chapter, self.current_selected_verse)

    def show_verse(self, book=None, chapter=None, verse=None):
        if not verse:
            self.verse_display.pack_forget()
            return

        self.current_selected_verse = verse
        self.current_selected_text = f"{book['name']} {chapter['chapter']}, {verse['verse']}:\n{verse['content']}"

        self.ref_label.configure(text=f"{book['name']} {chapter['chapter']}, {verse['verse']}:")

        max_width = self.left_frame.winfo_width() - 40
        if max_width <= 0:
            max_width = 800

        self.luther_label.configure(text=verse["content"], wraplength=max_width)

        book_num = book["book"]
        chap_key = chapter["chapter"]
        verse_key = verse["verse"]
        if book_num <= 39:
            chap_key = self.dec_to_hebrew(int(chapter["chapter"]))
            verse_key = self.dec_to_hebrew(int(verse["verse"]))
        original_text = self.original_lookup.get(book_num, {}).get(chap_key, {}).get(verse_key, "Text nicht verfügbar")
        self.original_label.configure(text=original_text, wraplength=max_width)

        if not self.verse_display.winfo_ismapped():
            self.verse_display.pack(fill="x", padx=10, pady=10)
        self.verse_display.update_idletasks()

    def copy_verse(self):
        if self.current_selected_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_selected_text)

    @staticmethod
    def dec_to_hebrew(num):
        if num == 15: return "טו"
        if num == 16: return "טז"
        values = [400,300,200,100,90,80,70,60,50,40,30,20,10,9,8,7,6,5,4,3,2,1]
        letters = ["ת","ש","ר","ק","צ","פ","ע","ס","נ","מ","ל","כ","י","ט","ח","ז","ו","ה","ד","ג","ב","א"]
        result = ""
        for i, val in enumerate(values):
            while num >= val:
                num -= val
                result += letters[i]
        return result

if __name__ == "__main__":
    app = BibleApp()
    app.root.mainloop()