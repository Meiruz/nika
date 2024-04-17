"""
This code creates some test agent and registers until the user stops the process.
For this we wait for SIGINT.
"""
import logging
from sc_client.models import ScAddr, ScLinkContentType, ScTemplate
from sc_client.constants import sc_types
from sc_client.client import template_search

from sc_kpm import ScAgentClassic, ScModule, ScResult, ScServer
from sc_kpm.sc_sets import ScSet
from sc_kpm.utils import (
    create_link,
    create_node,
    get_link_content_data,
    check_edge, create_edge,
    delete_edges,
    get_element_by_role_relation,
    get_element_by_norole_relation,
    get_system_idtf,
    get_edge
)
from sc_kpm.utils.action_utils import (
    create_action_answer,
    finish_action_with_status,
    get_action_arguments,
    get_element_by_role_relation
)
from wikipedia import *
from random import *
from sc_kpm import ScKeynodes

import haversine as hs
from haversine import Unit
import requests
API_KEY = '5b3ce3597851110001cf62484e61be75f1be4fd19569f26fa1371ce0'
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)

stations = [
    ["Малиновка", "Петровщина", "Михалово", "Грушевка", "Институт Культуры", "Площадь Ленина", "Октябрьская", "Площадь Победы", "Площадь Якуба Коласа", "Академия Наук", "Парк Челюскинцев", "Московская", "Восток", "Борисовский тракт", "Уручье"], 
    ["Могилевская", "Автозаводская", "Партизанская", "Тракторный завод", "Пролетарская", "Первомайская", "Купаловская", "Немига", "Фрунзенская", "Молодежная", "Пушкинская", "Спортивная", "Кунцевщина", "Каменная горка"], 
    ["Слуцкий Гостинец", "Неморшанский сад", "Аэродромная", "Ковальская Слобода", "Вокзальная", "Площадь Франтишка Богушевича", "Площадь Юбилейная"]
]

lines = ["Московская", "Автозаводская", "Зеленолужская"]
colors = ["rgb(38, 84, 141)", "rgb(150, 68, 68)", "rgb(68, 150, 68)"]


class FindMetroStationAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_show_find_metro_station")
        self.logger.info("FindMetroStationAgent Open %s")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("FindMetroStationAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        [message_addr] = get_action_arguments(action_node, 1)
        message_type = ScKeynodes.resolve(
                "concept_message_about_find_metro_station", sc_types.NODE_CONST_CLASS)
        self.logger.info("FindMetroStationAgent started")
        if not check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, message_type, message_addr):
            self.logger.info(
                f"FindMetroStationsAgent: the message isn’t about metro")
            return ScResult.OK

        rrel_first_place = ScKeynodes.resolve('rrel_first_place', sc_types.NODE_CONST_ROLE)
        rrel_second_place = ScKeynodes.resolve('rrel_second_place', sc_types.NODE_CONST_ROLE)

        # Получение данных (места от которого и до которого надо добраться)
        first_place_link_addr = self.get_entity_addr(message_addr, rrel_first_place)
        second_place_link_addr = self.get_entity_addr(message_addr, rrel_second_place)
        first_place = get_link_content_data(first_place_link_addr)
        second_place = get_link_content_data(second_place_link_addr)

        # Получение координат мест

        try:
            first = first_place
            second = second_place

            first_place = self.change_translate(first_place[3:].lower())
            second_place = self.change_translate(second_place[3:].lower())
            print(second_place)
            
            response1 = requests.get(f"https://nominatim.openstreetmap.org/search.php?q={first_place}, Минск&format=jsonv2").json()
            response2 = requests.get(f"https://nominatim.openstreetmap.org/search.php?q={second_place}, Минск&format=jsonv2").json()
            
            print(response1)

            ip_first_place = f"{response1[0]['lon']}, {response1[0]['lat']}"
            print("Ok")
            ip_second_place = f"{response2[0]['lon']}, {response2[0]['lat']}"
            print("Ok")


            print(f'{ip_first_place} {ip_second_place}');
        except:
            answer = choice([f'К сожалению, не удалось распознать, куда вам надо. {first_place} {second_place}.', f'Не распознано. {first_place} {second_place}.'])

            link = create_link(
                answer, ScLinkContentType.STRING, link_type=sc_types.LINK_CONST)
            edge = create_edge(sc_types.EDGE_D_COMMON_CONST, message_addr, link)
            create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes['nrel_answer'], edge)
            return ScResult.OK

        # Поиск ближайших точек входа и выхода в метро
        concept_metro_station = ScKeynodes.resolve('concept_metro_station', sc_types.NODE_CONST_CLASS)
        
        template = ScTemplate()
        template.triple(
            concept_metro_station,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            sc_types.NODE_VAR >> "_station",
        )

        template.triple_with_relation(
            '_station',
            sc_types.EDGE_D_COMMON_VAR,
            sc_types.NODE_VAR >> "_station_inputs",
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            ScKeynodes['nrel_inputs'],
        )

        template.triple(
            '_station_inputs',
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            sc_types.NODE_VAR >> "_station_input",
        )

        template.triple_with_relation(
            '_station_input',
            sc_types.EDGE_D_COMMON_VAR,
            sc_types.LINK_VAR >> "_coordinates",
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            ScKeynodes['nrel_coordinates'],
        )

        result = template_search(template)

        if len(result) == 0:
            self.logger.error('FindMetroStationAgent: There are no stations.')
            return ScResult.ERROR

        min_d_in = 9999999
        station_in = ''
        min_d_out = 9999999
        station_outs = ''

        for metro_input in result:
            coordinates_addr = metro_input.get('_coordinates')
            coordinates = get_link_content_data(coordinates_addr)
            metro_station_addr = metro_input.get('_station')
            metro_input_addr = metro_input.get('_station_input')

            # Получение расстояний до точки
            d_in = hs.haversine(self.return_coord(coordinates, 1), self.return_coord(ip_first_place), unit=Unit.KILOMETERS)
            d_out = hs.haversine(self.return_coord(coordinates, 1), self.return_coord(ip_second_place), unit=Unit.KILOMETERS)

            if d_in < min_d_in:
                min_d_in = d_in
                station_in = metro_station_addr

            if d_out < min_d_out:
                min_d_out = d_out
                station_out = metro_station_addr
        print(station_in)
        # Оформление вывода

        s1 = get_link_content_data(self.get_ru_idtf(station_in))
        s2 = get_link_content_data(self.get_ru_idtf(station_out))
        no = -1

        print(f'|{s1} {s2}|');

        if s1 in stations[0] and s2 in stations[0]:
            no = 0;
        elif s1 in stations[1] and s2 in stations[1]:
            no = 1;
        elif s1 in stations[2] and s2 in stations[2]:
            no = 2;
        
        answer = "";

        
        if no != -1:
            answer = f'<a href="https://metropoliten.by/upload/map4.jpg"><img style="max-width: 100%; width: 100%; margin-bottom: 8px; border-radius: 8px;" src="https://metropoliten.by/upload/map4.jpg"></img></a><p>Для того, чтобы добраться {first} {second} вам необходимо пройти к станции <a href="https://yandex.by/maps/21144/lida/search/метро {s1}" style="color: {colors[no]} !important">{s1}</a> и ехать до <a href="https://yandex.by/maps/21144/lida/search/метро {s2}" style="color: {colors[no]} !important">станции {s2}</a>.</p>'
        else:
            lineStart = ""
            lineEnd = ''
            k = ""

            if s1 in stations[0]:
                lineStart = lines[0]
                k += '1'
            elif s1 in stations[1]:
                lineStart = lines[1]
                k += '2'
            elif s1 in stations[2]:
                lineStart = lines[2]
                k += '3'

            if s2 in stations[0]:
                lineEnd = lines[0]
                k += '1'
            elif s2 in stations[1]:
                lineEnd = lines[1]
                k += '2'
            elif s2 in stations[2]:
                lineEnd = lines[2]
                k += '3'

            stationLine = "";
            print(k)

            if k == '12':
                stationLine = "Октябрьская"
            if k == '21':
                stationLine = "Купаловская"
            elif k == '23':
                stationLine = "Фрунзенская"
            elif k == '32':
                stationLine = "Площадь Юбилейная"
            elif k == '13':
                stationLine = "Площадь Ленина"
            elif k == '31':
                stationLine = "Вокзальная"
            answer += f'<div class="hover_image"><a href="https://metropoliten.by/upload/map4.jpg"><img style="max-width: 100%; width: 100; border-radius: 8px;" src="https://metropoliten.by/upload/map4.jpg"></img></div></a><p>Для того, чтобы добраться {first} {second} вам необходимо пройти к <a href="https://yandex.by/maps/21144/lida/search/метро {s1}" style="color: {colors[int(k[0])-1]} !important">станции {s1}</a> и ехать до <a href="https://yandex.by/maps/21144/lida/search/метро {s2}" style="color: {colors[int(k[1])-1]} !important">станции {s2}</a></p> Вам придется пересесть с линии <span style="color: {colors[int(k[0])-1]} !important">{lineStart}</span> на <span style="color: {colors[int(k[1])-1]} !important">{lineEnd}</span> на <a href="https://yandex.by/maps/21144/lida/search/метро {stationLine}" style="color: {colors[int(k[0])-1]} !important">странции {stationLine}</a>.';

        self.logger.info(f"FindMetroStationAgent: Answer: {answer}")

        link = create_link(
            answer, ScLinkContentType.STRING, link_type=sc_types.LINK_CONST)
        edge = create_edge(sc_types.EDGE_D_COMMON_CONST, message_addr, link)
        create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes['nrel_answer'], edge)

        return ScResult.OK

    def get_entity_addr(self, message_addr: ScAddr, rrel_entity: ScAddr):
        
        template = ScTemplate()
        template.triple_with_relation(
            message_addr,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            sc_types.VAR,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            rrel_entity,
        )
        search_results = template_search(template)
        
        if len(search_results) == 0:
            return ScAddr(0)
        
        return search_results[0][2]
    
    def get_ru_idtf(self, entity_addr: ScAddr) -> ScAddr:
        main_idtf = ScKeynodes.resolve(
            "nrel_main_idtf", sc_types.NODE_CONST_NOROLE)
        
        lang_ru = ScKeynodes.resolve("lang_ru", sc_types.NODE_CONST_CLASS)

        template = ScTemplate()
        template.triple_with_relation(
            entity_addr,
            sc_types.EDGE_D_COMMON_VAR,
            sc_types.LINK,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            main_idtf,
        )
        search_results = template_search(template)
        for result in search_results:
            idtf = result[2]
            lang_edge = get_edge(
                lang_ru, idtf, sc_types.EDGE_ACCESS_VAR_POS_PERM)
            if lang_edge:
                return idtf
        return get_element_by_norole_relation(
            src=entity_addr, nrel_node=main_idtf)



    def return_coord(self, str, oper = 0):
        ans = str.split(', ')

        if oper == 1:
            return float(ans[1]), float(ans[0])
        return float(ans[0]), float(ans[1])
    
    def change_translate(self, s):
        print(s)
        if s.find('улицы') > -1:
            s = s.replace('улицы', "улица")
        if s.find('проезда') > -1:
            s = s.replace('проезда', 'проезд')
        if s.find('проспекта') > -1:
            print("Found")
            s = s.replace('проспекта', 'проспект')
        if s.find('площади') > -1:
            s = s.replace('площади', 'площадь')
        if s.find('переулка') > -1:
            s = s.replace('переулка', 'переулок')

        if s.find('университетского') > -1:
            s = s.replace('университетского', 'университетский')
        return s
                