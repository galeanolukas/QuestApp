from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, NumericProperty
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from datetime import datetime
from kivy.core.text import Text
from kivy.uix.textinput import TextInput
from kivy.clock import mainthread, Clock
from kivy.utils import platform
from android_permisos import AndroidPermissions
from pathlib import Path
import os
from os.path import exists, join
from shutil import rmtree
import requests
import csv
import string
import random

if platform == 'android':
    from android import mActivity, autoclass, api_version
    from android.storage import primary_external_storage_path, app_storage_path
    from androidstorage4kivy import SharedStorage, Chooser
    Environment = autoclass('android.os.Environment')

def Key(digit=4):
    keylist = [random.choice(base_str()) for i in range(digit)]
    return ("".join(keylist))

def base_str():
    return (string.ascii_letters+string.digits)

def json2csv(file_name=None, json_data=None):
    csv_file = open(file_name, 'w')
    dict_update = {}
    preguntas = []
    respuestas = []
    for usuario in json_data:
        respuestas.append(json_data[usuario])
        dict_update["usuario"] = usuario
        json_data[usuario].update({"usuarios":usuario})
        for pregunta in json_data[usuario]:
            if pregunta in preguntas:
                break
            else:
                preguntas.append(pregunta)

    writer = csv.DictWriter(csv_file, fieldnames=preguntas)
    writer.writeheader()
    writer.writerows(respuestas)

    csv_file.close()

    return os.path.abspath(file_name)

class TextInputwHintSize(TextInput):
    hint_font_size = NumericProperty(30)

    def __init__(self, **kwargs):
        self.regular_font_size = 30
        self.ignore_font_size_change = False
        super(TextInputwHintSize, self).__init__(**kwargs)
        Clock.schedule_once(self.set_font_size)

    def set_font_size(self, dt):
        self.ignore_font_size_change = True
        if self.text == '':
            self.font_size = self.hint_font_size

    def on_font_size(self, instance, size):
        if self.ignore_font_size_change:
            return
        self.regular_font_size = size


    def on_text(self, instance, text):
        if text == '':
            self.font_size = self.hint_font_size
        else:
            self.font_size = self.regular_font_size

class AppPrincipal(App):

    def build(self):
        Window.clearcolor = (0, 133/255, 80/255, 1)
        if platform == 'android':
            temp = SharedStorage().get_cache_dir()
            if temp and exists(temp):
                rmtree(temp)

        return kv

    def on_start(self):
        self.dont_gc = AndroidPermissions(self.start_app)

    def start_app(self):
        self.dont_gc = None

    def update_font_size(self, widget):
        text = widget.text
        max_width = widget.width - (widget.border[1] + widget.border[3])
        max_height = widget.height - (widget.border[0] + widget.border[2])

        if not text:
            return
        instance = Text(text_size=(max_width, None), font_size=10, text=text)
        width, height = instance.render()

        while height < max_height:
            instance.options['font_size'] *= 2
            width, height = instance.render()

        while height > max_height:
            instance.options['font_size'] *= .95
            width, height = instance.render()

        widget.font_size = instance.options['font_size']
        self.reset_scroll(widget)

    @mainthread
    def reset_scroll(self, widget):
        widget.scroll_x = widget.scroll_y = 0

class WindowManager(ScreenManager):
    if platform == "android":
        share_storage = SharedStorage()
        path_to_save = app_storage_path()
        db = JsonStore(join(path_to_save, 'INTAPPDB.json'))
        download_dir = Environment.DIRECTORY_DOCUMENTS
    else:
        path_to_save = "/home/%s" % os.environ.get("USERNAME")
        download_dir = "Descargas/CHKApp"
        db = JsonStore('INTAPPDB.json')

    if db.exists("firebase_url"):
        try:
            json_db = requests.get(url=db.get("firebase_url")["link"]).json()
            for key in json_db:
                if key == "firebase_url":
                    if db.get(key)["link"] != json_db[key]["link"]:
                        db.put(key, link=json_db[key]["link"])
                else:
                    pass

        except requests.exceptions.JSONDecodeError as e:
            pass

        except requests.exceptions.ConnectionError as e:
            pass
    else:
        db.put("firebase_url",link="https://intaapp-86055-default-rtdb.firebaseio.com/.json")

    firebase_url = db.get("firebase_url")["link"]
    user = None
    user_id = None
    key_admin = None
    update_notif = ""
    pregunta_uno = None
    pregunta_dos = None
    pregunta_tres = None
    pregunta_cuatro = None
    fecha_y_hora = None
    modo = None

    def check_admin(self, instance_input):
        try:
            json_db = requests.get(url=self.firebase_url).json()
            if instance_input in json_db:
                self.key_admin = instance_input
                return self.key_admin
            else:
                return instance_input

        except requests.exceptions.JSONDecodeError as e:
            return instance_input
        except requests.exceptions.ConnectionError as e:
            return instance_input

    def actualizar_db(self):
        try:
            json_db = requests.get(url=self.firebase_url).json()
            if json_db is None:
                return False
            else:
                for key in self.db:
                    if key in json_db:
                        pass
                    else:
                        if key == "firebase_url":
                            pass
                        else:
                            data = {key: self.db.get(key)}
                            update_json = requests.patch(url=self.firebase_url, json=data)
                            update_json.close()

                return True

            self.update_notif = "DB ACTUALIZADA %s" % datetime.now().strftime("%d:%m:%Y %H:%m")

        except requests.exceptions.JSONDecodeError as e:
            pass
        except requests.exceptions.ConnectionError as e:
            self.update_notif = "DB NO ACTUALIZADA"
            return False


class VentanaInicio(Screen):
    update_db = WindowManager().actualizar_db()
    entrada_login = ObjectProperty(None)
    mode = ObjectProperty(None)
    boton_init = ObjectProperty(None)
    debug = ObjectProperty(None)

    def validar(self):
        if self.entrada_login.text != "":
            return True
        else:
            return False

    def siguiente(self, instance):
        if self.validar():
            instance.user_id = "%s_%s" % (str(self.entrada_login.text), Key(6))
            instance.user = instance.check_admin(self.entrada_login.text)
            self.debug.text = "Actualizando DB..."
            self.boton_init.disabled = True
            #instance.actualizar_db()
            self.boton_init.disabled = False
            if instance.key_admin:
                self.debug.text = ""
                instance.current = "admin_login"
                instance.transition.direction = "right"

            else:
                self.debug.text = ""
                instance.current = "pregunta_uno"
                instance.transition.direction = "left"


        else:
            self.debug.text = "Debes ingresar nombre o id"

    def volver(self, instance):
        instance.current = "inicio"
        instance.transition.direction = "right"
        self.debug.text = ""

class VentanaAdmin(Screen):
    pass_login = ObjectProperty(None)
    debug = ObjectProperty(None)

    def validar(self, instance, clave):
        try:
            json_db = requests.get(url=instance.firebase_url).json()
            if json_db is None:
                return False
            else:
                if json_db[instance.user]["clave"] == clave:
                    instance.current = "final_admin"
                    instance.transition.direction = "right"
                    return True
                else:
                    self.debug.text = "Clave incorrecta!!"
                    return False

        except requests.exceptions.JSONDecodeError as e:
            self.debug.color = "#ff1100"
            instance.debug.text = "Erro! base de datos invalida!"
            return False

        except requests.exceptions.ConnectionError as e:
            self.debug.color = "#ff1100"
            instance.debug.text = "No hay conexion a Internet!! :("
            return False

    def volver(self, instance):
        instance.current = "inicio"
        instance.transition.direction = "left"
        instance.key_admin = None
        self.debug.text = ""

class VentanaAdminConfig(Screen):
    link_db = ObjectProperty(None)
    debug = ObjectProperty(None)

    def backup_db_data(self, instance, db_nueva):
        tmp_db_data = {}
        try:
            json_db = requests.get(url=instance.firebase_url).json()
            for key in json_db:
                if key == "firebase_url":
                    tmp_db_data[key] = {"link":db_nueva}
                else:
                    tmp_db_data[key] = json_db[key]

            return tmp_db_data

        except Exception:
            return None

    def cambiar(self, instance):
        if self.link_db.text:
            try:
                db_nueva = self.link_db.text + ".json"
                js_db = requests.patch(url=db_nueva, json=self.backup_db_data(instance, db_nueva))
                instance.db.put("firebase_url", link=db_nueva)
                instance.firebase_url = db_nueva
                self.debug.text = 'Exito! "%s" al cambiar su DB!!' % instance.key_admin

            except requests.exceptions.ConnectionError as e:
                self.debug.color = "#ff1100"
                self.debug.text = "Error! No se pudo conectar: %s" % e
        else:
            self.debug.text = "Debes ingresar el link!"

    def volver(self, instance):
        instance.current = "inicio"
        instance.transition.direction = "left"
        instance.key_admin = None
        self.debug.text = ""

class VentanaPregunta1(Screen):
    preg_uno = ObjectProperty(None)
    debug = ObjectProperty(None)
    mode = ObjectProperty(None)
    v_manager = WindowManager()
    respuestas = []

    def get_checks(self, instance, value, topping):
        if value == True:
            if topping in self.respuestas:
                pass
            else:
                self.respuestas.append(topping)

        else:
            if topping in self.respuestas:
                self.respuestas.remove(topping)
            else:
                pass

    def validar(self):
        if len(self.respuestas) != 0:
            return True
        else:
            return False

    def siguiente(self, instance):
        if self.validar():
            instance.pregunta_uno = self.respuestas
            instance.current = "pregunta_dos"
            instance.transition.direction = "left"
            self.debug.text = ""
        else:
            instance.current = "pregunta_uno"
            self.debug.text = "Debes marcar alguna de las respuestas!"
            pass

    def volver(self, instance):
        instance.current = "inicio"
        instance.transition.direction = "right"
        self.debug.text = ""

class VentanaPregunta2(Screen):
    debug = ObjectProperty(None)
    preg_dos = ObjectProperty(None)
    mode = ObjectProperty(None)
    v_manager = WindowManager()
    respuesas = []

    def validar(self):
        if self.preg_dos.text != "":
            return True
        else:
            return False

    def siguiente(self, instance):
        if self.validar():
            instance.pregunta_dos = self.preg_dos.text
            instance.current = "pregunta_tres"
            instance.transition.direction = "left"
            self.debug.text = ""
        else:
            instance.current = "pregunta_dos"
            self.debug.text = "Debes ingresar número como respuesta!"
            pass

    def volver(self, instance):
        instance.current = "pregunta_uno"
        instance.transition.direction = "right"
        self.debug.text = ""


class VentanaPregunta3(Screen):
    debug = ObjectProperty(None)
    preg_tres = ObjectProperty(None)
    mode = ObjectProperty(None)
    v_manager = WindowManager()

    def validar(self):
        if self.preg_tres.text != "":
            return True
        else:
            return False

    def siguiente(self, instance):
        if self.validar():
            instance.pregunta_tres = self.preg_tres.text
            instance.current = "pregunta_cuatro"
            instance.transition.direction = "left"
            self.debug.text = ""

        else:
            instance.current = "pregunta_tres"
            self.debug.text = "Debes ingresar una respuesta!"
            pass

    def volver(self, instance):
        instance.current = "pregunta_dos"
        instance.transition.direction = "right"
        self.debug.text = ""

class VentanaPregunta4(Screen):
    debug = ObjectProperty(None)
    preg_cuatro = ObjectProperty(None)
    mode = ObjectProperty(None)
    v_manager = WindowManager()
    respuestas = []

    def get_checks(self, instance, value, topping):
        if value == True:
            if topping in self.respuestas:
                pass
            else:
                self.respuestas.append(topping)
        else:
            if topping in self.respuestas:
                self.respuestas.remove(topping)
            else:
                pass


    def validar(self):
        if len(self.respuestas) != 0:
            return True
        else:
            return False

    def siguiente(self, instance):
        if self.validar():
            instance.pregunta_cuatro = self.respuestas
            instance.current = "final"
            instance.transition.direction = "left"
            self.debug.text = ""

        else:
            instance.current = "pregunta_cuatro"
            self.debug.text = "Debes marcar al menos una casilla!"


    def volver(self, instance):
        instance.current = "pregunta_tres"
        instance.transition.direction = "right"


class VentanaFinal(Screen):
    debug = ObjectProperty(None)
    mode = ObjectProperty(None)
    enviar = ObjectProperty(None)

    def guardar_enviar(self, instance):
        instance.db.put(instance.user_id,
                        usuario=instance.user,
                        pregunta_uno=instance.pregunta_uno,
                        pregunta_dos=instance.pregunta_dos,
                        pregunta_tres=instance.pregunta_tres,
                        pregunta_cuatro=instance.pregunta_cuatro,
                        fecha_y_hora=datetime.now().strftime("%d/%m/%Y %H:%m"))

        if instance.actualizar_db():
            self.debug.color = "#00FF48FF"
            self.debug.text = 'Tus datos se guardaron con exito!'
        else:
            self.debug.text = 'Tus datos se han guardado solo en el telefono!'
            instance.transition.direction = "left"
            self.enviar.disabled = False

    def volver(self, instance):
        instance.current = "pregunta_cuatro"
        instance.transition.direction = "right"
        self.debug.text = ""

    def terminar(self, instance):
        instance.stop()
        Window.close()

#Ventana admin save
class VentanaFinalAdmin(Screen):
    debug = ObjectProperty(None)
    mode = ObjectProperty(None)

    def descargar_csv(self, instance):
        self.debug.font_size = 20
        try:
            json_db = requests.get(url=instance.firebase_url).json()
            json_db.pop(instance.key_admin)
            json_db.pop("firebase_url")
            filename = os.path.join(instance.path_to_save, 'ENCUESTA_INTA_2023.csv')
            file_path = json2csv(filename, json_db)
            if platform == 'android':
                instance.share_storage.copy_to_shared(filename, collection = instance.download_dir)
                self.debug.text = "Exito!! CSV en Documentos"
            else:
                self.debug.text = "Exito!! CSV en %s" % instance.download_dir

        except requests.exceptions.ConnectionError as e:
            self.debug.color = "#ff1100"
            self.debug.text = "Error! No se pudo obtener datos de la db"

        except PermissionError as e:
            self.debug.color = "#ff1100"
            self.debug.text = "%s" % e

    def config_db(self, instance):
        instance.current = "admin_config"
        instance.transition.direction = "right"

    def change_admin_pass(self, instance):
        try:
            data = {instance.key_admin: json_db[instance.key_admin]}
            del_json_db = requests.patch(url=instance.firebase_url, json=data)
            self.debug.text = "Exito!! se ha cambiado la clave admin"

        except requests.exceptions.ConnectionError as e:
            self.debug.color = "#ff1100"
            self.debug.text = "Error! No se pudo obtener datos de la db"
            pass

    def volver(self, instance):
        instance.current = "inicio"
        instance.transition.direction = "left"
        instance.key_admin = None
        self.debug.text = ""


if __name__ == "__main__":
    kv = Builder.load_file("main.kv")
    AppPrincipal().run()
