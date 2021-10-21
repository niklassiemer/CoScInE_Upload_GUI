import io
import os
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
import tkinter as tk
from tkinter import Tk, ttk, constants as tk_const, filedialog, scrolledtext
from coscine import Client
from coscine.exceptions import RequirementError, ServerError, UnauthorizedError, VocabularyError

COLOR = {
    "green": "#89c98a",
    "blue": "#6988fa"
}


class CoscineWrapper:
    def __init__(self, project):
        """
        project(coscine.project/coscine.client):
        """
        if hasattr(project, 'client'):
            self._project = project
            self._client = project.client
        else:
            self._project = None
            self._client = project

        if self._client.verbose:
            print("Silenced client!")
            self._client.verbose = False

    @property
    def verbose(self):
        return self._client.verbose

    @verbose.setter
    def verbose(self, val):
        self._client.verbose = val

    def list_groups(self):
        if self._project is None:
            return [pr.name for pr in self._client.projects()]
        else:
            return [pr.name for pr in self._project.subprojects()]

    def list_nodes(self):
        if self._project is None:
            return []
        else:
            return [res.name for res in self._project.resources()]

    def __getitem__(self, key):
        if key in self.list_nodes():  # This implies project is not None
            return self._project.resource(key)
        self.get_group(key)

    def get_node(self, key):
        if key in self.list_nodes():
            return self._project.resource(key)
        else:
            return KeyError(key)

    def get_group(self, key):
        if key in self.list_groups() and self._project is not None:
            return self.__class__(self._project.subprojects(displayName=key)[0])
        elif key in self.list_groups():
            return self.__class__(self._client.project(key))
        else:
            raise KeyError(key)


class TkinterOutput:
    def __init__(self, parent_widget, scrolling=False):
        self._text = ""
        self._scrolling = scrolling
        if scrolling:
            self._output = scrolledtext.ScrolledText(parent_widget)
            self._output.insert(tk_const.INSERT, self._text)
            self._output.configure(state=tk_const.DISABLED)
        else:
            self._output = tk.Label(parent_widget)

    @property
    def output(self):
        return self._output

    def write(self, string, mode='a', newline=True):
        if mode == 'w':
            self._text = ""
        elif mode == 'a' and newline:
            self._text += '\n'
        if isinstance(string, str):
            self._text += string
        else:
            self._text += str(string)

        self._update()

    def _update(self):
        if self._scrolling:
            self._output.configure(state=tk_const.NORMAL)
            self._output.delete('1.0', tk_const.END)
            self._output.insert(tk_const.INSERT,
                                self._text)
            self._output.see(tk_const.END)
            self._output.configure(state=tk_const.DISABLED)
        else:
            self._output['text'] = self._text

    def clear_output(self):
        self._text = ""
        self._update()

    def capture_stdout(self, func, *args, **kwargs):
        store_stream = io.StringIO()
        with redirect_stdout(store_stream):
            func(*args, **kwargs)
        self.write(store_stream.getvalue(), mode='w')

    def capture_stderr(self, func, *args, **kwargs):
        store_stream = io.StringIO()
        old_tell = store_stream.tell()
        with redirect_stderr(store_stream):
            try:
                th = threading.Thread(target=func, args=args, kwargs=kwargs)
                th.start()
            except Exception as e:
                self.write(e.args[0])
                raise e
            while th.is_alive():
                time.sleep(0.01)
                current_tell = store_stream.tell()
                if current_tell > old_tell:
                    val = store_stream.getvalue()[old_tell:current_tell]
                    old_tell = current_tell
                    self.write(val, mode='w')
        th.join()


class TKInterApplication:
    def __init__(self):
        self._root = Tk(className="CoScInE Upload")
        self._main_frm = ttk.Frame(self._root, padding=10)

        self._frm = ttk.Frame(self._main_frm)

        self._output_frm = ttk.Frame(self._main_frm)
        self._output = TkinterOutput(self._output_frm)
        self._error = TkinterOutput(self._output_frm)
        self._layout()

        self._init_hook()

        self._root.mainloop()

    def _layout(self):
        self._main_frm.grid()
        self._frm.grid(column=0, row=0, columnspan=3, sticky=tk_const.NW)
        self._output_frm.grid(column=4, row=0)
        self._output.output.grid()
        self._error.output.grid()

    def _init_hook(self):
        pass

    def _clear_output(self):
        self._error.clear_output()
        self._output.clear_output()

    def _reset_body_frame(self):
        self._frm.destroy()
        self._frm = ttk.Frame(self._main_frm)
        self._frm.grid(column=0, row=0)

    def _gen_button_frame(self, master, names, func, values=None, color=None, ncol=1, nrow=None):
        if isinstance(names, str):
            names = [names]
        elif not isinstance(names, list):
            raise ValueError
        frame = ttk.Frame(master)
        if ncol is None:
            ncol = len(names)
        if nrow is not None and len(names) > ncol * nrow:
            raise ValueError

        if values is not None and len(values) != len(names):
            raise ValueError
        elif values is None:
            values = [name for name in names]

        for i, name_value in enumerate(zip(names, values)):
            name = name_value[0]
            value = name_value[1]
            button = tk.Button(frame, text=name, command=lambda val=value: func(val))
            col = i % ncol
            row = int((i - col) / ncol)
            button.grid(column=col, row=row)
            if color is not None:
                button.configure(bg=color)

        return frame


class UploadPopUp(TKInterApplication):
    def __init__(self, res, filename, file_to_upload, metadata):
        self._res = res
        self._filename = filename
        self._file_to_upload = file_to_upload
        self._metadata = metadata
        self._chunksize = None
        self._th = None
        super().__init__()

    def _layout(self):
        self._main_frm.grid()
        self._frm.grid(column=0, row=0, sticky=tk_const.NW)
        self._output_frm.grid(column=0, row=2, sticky=tk_const.NW)
        self._output.output.grid()
        self._error.output.grid()

    def _init_hook(self):
        label = tk.Label(self._frm, text=f"Uploading {self._file_to_upload} to {self._res.name}/{self._filename}.")
        label.grid(row=0, column=0)
        self._cancel_button = tk.Button(self._frm, text="Cancel", command=self._cancel)
        self._cancel_button.grid(row=0, column=1)

        self._init_upload()

    def _upload_thread(self):
        self._res.client.verbose = True
        self._error.capture_stderr(self._res.upload,
                                   self._filename,
                                   self._file_to_upload,
                                   self._metadata)

        self._res.client.verbose = False

    def _check_thread(self):
        while self._th.is_alive():
            time.sleep(0.5)
        self._cancel_button['text'] = 'Done'

    def _init_upload(self):
        self._th = threading.Thread(target=self._upload_thread)
        self._th.start()
        time.sleep(0.5)
        th2 = threading.Thread(target=self._check_thread)
        th2.start()

    def _cancel(self):
        self._root.destroy()


class CoScInEGUI(TKInterApplication):
    def __init__(self, client_wrapper: CoscineWrapper):
        self._history = [client_wrapper]
        self._history_idx = 0
        self._project = client_wrapper
        self._meta_data_dict = {}
        self._file_to_upload = None
        self._res = None
        self._path_list = ['/']
        super().__init__()

    def _load_history(self, hist_idx=None):
        if hist_idx is not None:
            self._history_idx = hist_idx
        self._project = self._history[self._history_idx]
        self._init_select_resource_gui()

    def _go_back(self):
        self._history_idx -= 1
        self._load_history()

    def _go_forward(self):
        self._history_idx += 1
        self._load_history()

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, new_project):
        self._project = new_project
        self._history_idx += 1
        self._history = self._history[:self._history_idx]
        self._path_list = self._path_list[:self._history_idx]
        self._history.append(self.project)
        self._init_select_resource_gui()

    @property
    def path_list(self):
        return self._path_list[:self._history_idx+1]

    def _init_hook(self):
        self._init_select_resource_gui()

    def _init_select_resource_gui(self):
        self._reset_body_frame()
        self._clear_output()
        self._gen_control_buttons()
        self._gen_project_buttons()
        self._gen_resource_buttons()

    def _gen_control_buttons(self):
        frm = ttk.Frame(self._frm)
        but = tk.Button(frm, text='<-', command=self._go_back, bg=COLOR['green'])
        but.grid(row=0, column=0)
        if self._history_idx == 0:
            but.configure(state=tk_const.DISABLED)

        but = tk.Button(frm, text='->', command=self._go_forward, bg=COLOR['green'])
        if self._history_idx == len(self._history)-1:
            but.configure(state=tk_const.DISABLED)
        but.grid(row=0, column=1)

        frm2 = self._gen_button_frame(frm, self.path_list, self._load_history, values=list(range(len(self.path_list))),
                                      ncol=None, color=COLOR['green'])
        frm2.grid(row=0, column=2)
        frm.grid(row=0, sticky=tk_const.W)
        return frm

    def _gen_project_buttons(self):
        frm = self._gen_button_frame(self._frm, self._project.list_groups(), self._on_project_clicked, ncol=5,
                                     color=COLOR["blue"])
        frm.grid(row=1, sticky=tk_const.W)
        return frm

    def _gen_resource_buttons(self):
        frm = self._gen_button_frame(self._frm, self._project.list_nodes(), self._on_resource_clicked, ncol=5)
        frm.grid(row=2, sticky=tk_const.W)
        return frm

    def _on_project_clicked(self, project):
        self.project = self._project.get_group(project)
        self._path_list.append(project)
        self._init_select_resource_gui()

    def _on_resource_clicked(self, resource):
        self._res = self._project.get_node(resource)
        self._init_upload_gui()

    def _res_overview_2_output(self):
        self._output.clear_output()
        info_text = f'{self._res.name}\n===========================\n'
        for obj in self._res.objects():
            info_text += f' {obj.name}  {obj.size}\n'
        self._output.write(info_text)

    def _init_upload_gui(self):
        self._reset_body_frame()
        self._clear_output()
        control_panel = self._gen_control_buttons()
        tk.Button(control_panel, text=self._res.name, bg=COLOR['green']).grid(row=0, column=3)
        self._meta_data_form = self._res.MetadataForm()
        frm = self._init_meta_data_form_gui()
        self._res_overview_2_output()
        frm.grid(row=1, sticky=tk_const.W)

        tk.Button(self._frm, text='Select file', command=self._get_filenames).grid(row=2, column=0)
        self._file_name = ttk.Entry(self._frm)
        self._file_name.grid(row=2, column=1)
        tk.Button(self._frm, text="Upload", command=self._upload_file).grid(row=3)

    def _upload_file(self):
        self._error.clear_output()
        form_str = self._parse_meta_data_dict()
        if form_str is None:
            return
        if self._file_to_upload is None:
            self._error.write("No file chosen!")
            return
        filename = self._file_name.get()
        if filename in [obj.name for obj in self._res.objects()]:
            self._error.write("File already present on CoScInE! Canceled")
            return
        upload = UploadPopUp(self._res, filename, self._file_to_upload, self._meta_data_form)
        self._res_overview_2_output()

    def _parse_meta_data_dict(self):
        for key, entry in self._meta_data_dict.items():
            entry_ = entry.get()
            if len(entry_) > 0:
                self._meta_data_form[key] = entry_
        try:
            form_str = self._meta_data_form.generate()
        except (RequirementError, VocabularyError) as e:
            self._error.write(e.args[0])
            return None
        return form_str

    def _get_filenames(self):
        file = filedialog.askopenfilename()
        filename = os.path.basename(file)
        self._file_to_upload = file
        self._file_name.delete(0, tk_const.END)
        self._file_name.insert(0, filename)
        self._error.write('loaded: ' + file)

    def _init_meta_data_form_gui(self):
        frm = ttk.Frame(self._frm)
        self._meta_data_dict = {}
        for i, key in enumerate(self._meta_data_form.keys()):
            if self._meta_data_form.is_required(key):
                tk.Label(frm, text='R', bg='red').grid(row=i, column=0)
            ttk.Label(frm, text=key).grid(row=i, column=1)
            if self._meta_data_form.is_controlled(key):
                value_dict = self._meta_data_form.get_vocabulary(key)
                self._meta_data_dict[key] = ttk.Combobox(frm, values=list(value_dict.keys()))
            else:
                self._meta_data_dict[key] = ttk.Entry(frm)
            self._meta_data_dict[key].grid(row=i, column=2)
        return frm


class CoScInETokenGUI(TKInterApplication):
    def _init_hook(self):
        self._init_token_frame()

    def _layout(self):
        self._main_frm.grid()
        self._output_frm.grid(column=4, row=0)
        self._frm.grid(column=0, row=0, columnspan=3, sticky=tk_const.NW)
        self._error.output.grid()

    def _get_token_from_file(self):
        token_file = filedialog.askopenfilename()
        if not os.path.isfile(token_file):
            return
        with open(token_file) as f:
            self._pwd = f.read()
        self._submit_click()

    def _init_token_frame(self):
        self._reset_body_frame()
        self._pwd = None
        ttk.Label(self._frm, text="CoScInE upload!").grid(column=0, row=0)
        ttk.Label(self._frm, text="API token:").grid(column=0, row=1)
        tk.Button(self._frm, text='Upload token', command=self._get_token_from_file).grid(column=1, row=2)
        self._pw_entry = ttk.Entry(self._frm, show='*')
        self._pw_entry.grid(column=1, row=1)
        self._button = tk.Button(self._frm, text="Submit", command=self._submit_click)
        self._button.grid(column=0, row=3)

    def _submit_click(self):
        self._error.write('Submit clicked')
        pwd = self._pw_entry.get()
        if self._pwd is None:
            self._pwd = pwd
        elif len(pwd) > 0:
            self._error.write('Error: Token provided in two ways.')
            self._init_token_frame()
            return

        self._client = Client(token=self._pwd, verbose=False)
        del self._pwd

        if self._client is not None:
            try:
                self._reset_body_frame()
                ttk.Label(self._frm, text="Connecting...")
                self._client.projects()
            except (ServerError, UnauthorizedError) as e:
                self._error.write(f"Error: {e.args[0]}")
                self._client = None
                self._init_token_frame()
            else:
                self._root.destroy()
                client_wrapper = CoscineWrapper(self._client)
                CoScInEGUI(client_wrapper)


CoScInETokenGUI()

