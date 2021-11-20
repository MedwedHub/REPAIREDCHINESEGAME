import datetime
import pprint
import random
import threading
import socket
import pickle
import time
from multiprocessing import Process, Manager


class Server:
    def __init__(self, machine_id):
        self.id = machine_id
        self.HOST = ''
        self.PORT = 27015
        self.ADDRESS = (self.HOST, self.PORT)
        self.BUFFERSIZE_TEMPORARY = 3072

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDRESS)
        self.server.listen(10)

        self.bots_list = []
        self.bots_processing_list = []
        self.bots_data_collection = []
        self.exit_is_set = False

    def server_message(self, text):
        print(datetime.datetime.now().time(), 'Сервер:', text)

    def data_accepting(self):
        message_time = time.time()
        message_time_cooldown = 120
        while not self.exit_is_set:
            # try:
            if self.bots_list:
                for bot in self.bots_list.copy():
                    if bot not in self.bots_processing_list:
                        threading.Thread(target=self.data_rcv, args=(bot,)).start()
                        #self.data_rcv(bot)
            else:
                if time.time() - message_time >= message_time_cooldown:
                    self.server_message('Сервер пуст.')
                    message_time = time.time()
            # except:
            #     self.server_message('ОШИБКА ОТПРАВКИ ДАННЫХ.')
            #     self.bots_list.clear()
            #     self.bots_processing_list.clear()

    def data_rcv(self, b):
        self.bots_processing_list.append(b)
        #try:
        data_ = b.recv(self.BUFFERSIZE_TEMPORARY)

        if data_:
            decoded_data = pickle.loads(data_)
            print(datetime.datetime.now().time(), decoded_data)
            self.send_data(data_)
            self.bots_processing_list.remove(b)
        # except:
        #     try:
        #         self.bots_processing_list.remove(b)
        #         b.close()
        #         self.bots_list.remove(b)
        #         self.server_message(f'Клиент удалён.')
        #     except ValueError:
        #         print('Клиент не в списке!!! Вот и всё...', ValueError)

    def send_data(self, data):
        for bot_ in self.bots_list:
            try:
                bot_.send(data)
            except:
                self.server_message('Ошибка передачи данных')
                bot_.close()
                self.bots_list.remove(bot_)
                self.server_message(f'Клиент удалён.')

    def bots_accepting(self):
        self.server_message('Сервер запущен.')
        while not self.exit_is_set:
            clientsocket, address = self.server.accept()
            self.bots_list.append(clientsocket)
            self.server_message('Бот установил связь.')

    def server_start(self):
        t1 = threading.Thread(target=self.bots_accepting)
        t1.start()
        self.data_accepting()


class Client:
    def __init__(self, machine_id, dtt, dtr, is_connected, server_item, ip=None):
        manager = Manager()
        self.id = machine_id
        self.HOST = '84.237.53.150'
        # self.HOST = '213.127.70.95'

        self.dtt = dtt
        self.dtr = dtr

        self.PORT = 27015
        self.ADDRESS = (self.HOST, self.PORT)
        self.BUFFERSIZE_TEMPORARY = 3072
        self.server = server_item
        self.server[0] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.connected_m = manager.list()
        #self.connected_m.append(False)
        self.connected_m = is_connected
        self.connected = False
        self.reconnected = False
        self.has_received = False
        self.tries = 0
        self.exit_is_set = False
        self.count = 0

        self.bots_list = []
        # manager = Manager()
        # self.bots_data_collection = manager.list()
        # self.bots_data_collection.append(0)
        self.bots_data_collection = {}

        self.conn()

    def connect(self):
        #while not self.connected and not self.exit_is_set:
        while not self.connected_m[0] and not self.exit_is_set:
            if self.tries >= 2:
                self.connected_m[0] = False
                #self.connected = False
                self.client_message('Сервер не отвечает. Работаем в оффлайн режиме')
                self.tries = 0
                break
            try:
                self.server[0].connect(self.ADDRESS)
                #self.connected = True
                self.connected_m[0] = True
                self.client_message('Соединение установлено')
                self.reconnected = False
                self.data_accepting_thread()
            except:
                self.client_message(
                    'Сервер не отвечает. Для технической поддержки, свяжитесь с Баганцем. Скорее всего, вы просто '
                    'дилетант. АЙПИ ИЗМЕНИЛ? САМ СЕРВЕР ЗАПУЩЕН??? Ну вот и всё.')
                self.tries += 1
                self.client_message(f'Попытка подключения {self.tries}')
                time.sleep(15)

    def autoconnect(self):
        while True:
            #print('autoconnect self.connected_m[0]', self.connected_m[0])
            #print('outer self.connected', self.connected)
            if not self.connected_m[0]:
            #if not self.connected:
                self.client_message('________________ВОЗНИКЛИ ПРОБЛЕМЫ С СОЕДИНЕНИЕМ. ЗАПУЩЕНО АВТОПОДКЛЮЧЕНИЕ________________')
                #while not self.reconnected:
                #print('reconnection...')
                #print('inner self.connected', self.connected)
                self.server[0] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connect()
            else:
                time.sleep(15)

    def is_connected(self):
        #return self.connected
        return self.connected_m[0]

    def client_message(self, text):
        print(datetime.datetime.now().time(), f'Бот {self.id}', text)

    def client_send(self, data_tt, key=None):
        if key is None:
            data_to_encode = {self.id: data_tt}
        else:
            data_to_encode = {key: data_tt}
        encoded_data_to_send = pickle.dumps(data_to_encode)
        print("LEN OF DATA", len(encoded_data_to_send))
        if self.connected_m[0]:
        #if self.connected:
            try:
                #print('client_send', self.count)
                self.server[0].send(encoded_data_to_send)
            except:
                self.client_message('ОШИБКА ОТПРАВКИ ДАННЫХ')
                self.server[0].close()
                #self.connected = False
                self.connected_m[0] = False
                # self.autoconnect()

    def client_receive_message(self):
        # self.dtr[0] = self.bots_data_collection
        # print('BOTNET dtr', self.dtr[0])
        # print('BOTNETdata_collection ', self.bots_data_collection)
        self.has_received = True
        # return self.dtr[0]

    def data_accepting(self):
        while not self.exit_is_set:
            if self.connected_m[0]:
                try:
                    if self.has_received:
                        self.bots_data_collection.clear()
                        # self.bots_data_collection[0] = 0
                        self.has_received = False

                    data_ = self.server[0].recv(self.BUFFERSIZE_TEMPORARY)

                    if data_:
                        decoded_data = pickle.loads(data_)
                        self.dtr[0] = decoded_data
                        self.bots_data_collection = decoded_data
                        # time.sleep(0.01)
                        # print('CLIENT', self.bots_data_collection)

                except:
                    self.client_message('ОШИБКА ПРИНЯТИЯ ДАННЫХ')
                    self.server[0].close()
                    #self.connected = False
                    self.connected_m[0] = False
                    # self.autoconnect()

    def data_accepting_thread(self):
        t1 = threading.Thread(target=self.data_accepting)
        t1.start()

    def conn(self):
        t2 = threading.Thread(target=self.autoconnect)
        t2.start()


if __name__ == '__main__':
    s = Server(1)
    s.server_start()

    # time.sleep(10)

    #c = Client(1, [0], [0], [0], [0])
    # c.connect_to_server()
