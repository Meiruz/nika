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
from sc_kpm import ScKeynodes

import requests
from random import randint, choice
API_KEY = '5b3ce3597851110001cf62484e61be75f1be4fd19569f26fa1371ce0'


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class TravellingAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_show_travelling")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("TravellingAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("TravellingPlacesAgent started")

        try:
            [message_addr, user_addr] = get_action_arguments(action_node, 2)
            message_type = ScKeynodes.resolve(
                "concept_message_about_travelling", sc_types.NODE_CONST_CLASS)

            if not check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, message_type, message_addr):
                self.logger.info(
                    f"FindSomePlacesAgent: the message isn't about weather")
                return ScResult.OK
            
            idtf = ScKeynodes.resolve("nrel_idtf", sc_types.NODE_CONST_NOROLE)
            answer_phrase = ScKeynodes.resolve(
                "show_travelling_answer_phrase", sc_types.NODE_CONST_CLASS)
            rrel_city_place = ScKeynodes.resolve("rrel_city_place", sc_types.NODE_ROLE)
            nrel_attractions = ScKeynodes.resolve(
                "nrel_attraction_message", sc_types.NODE_NOROLE)

            city_addr = self.get_entity_addr(
                message_addr, rrel_city_place)

            self.clear_previous_answer(
                city_addr, nrel_attractions, answer_phrase)
                
            # if there is no such сity
            if not city_addr.is_valid():
                self.logger.info(f"City not valid")
                self.set_unknown_city_link(action_node, answer_phrase)
                return ScResult.OK
            city_idtf_link = self.get_ru_idtf(city_addr)
            if not city_idtf_link.is_valid():
                self.logger.info(f"City_idtf not valid")
                self.set_unknown_city_link(action_node, answer_phrase)
                return ScResult.OK
        except:
            self.logger.info(f"TravellingAgent: finished with an error")
            return ScResult.ERROR

        city_idtf = get_link_content_data(city_idtf_link)
        s1 = f'<p>В городе {city_idtf} вы можете посетить:</p>'
        s2 = f'<p>Места города {city_idtf}, которые вы можете посетить:</p>'
        phrases = [s1, s2]
        n = randint(0, len(phrases)-1)
        
        attractions = phrases[n]
        

        template = ScTemplate()
        template.triple_with_relation(
            user_addr,
            sc_types.EDGE_D_COMMON_VAR,
            sc_types.NODE_VAR >> '_desires_addr',
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            ScKeynodes['nrel_desires'],
        )
        template.triple(
            '_desires_addr',
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            sc_types.NODE_VAR_CLASS >> '_desire_addr',
        )

        result = template_search(template)
        if len(result) == 0:
            self.logger.info('TravellingAgent: There is no desires in user.')
            return ScResult.ERROR
        
        desires = []
        for desire in result:
            desire_addr = desire.get('_desire_addr')
            desires.append(self.get_ru_idtf(desire_addr))
            
        latCoordString = ''
        lonCoordString = ''
        attraction = []
        kol = 0
        
        try:
            coordinates = requests.get(
                    f'https://geocode.maps.co/search?city={city_idtf}&country=Беларусь').json()[0]
            
            # We need take from kb a city with english lang
            city = coordinates['display_name'].split(',')[0]

            
            minx = coordinates['boundingbox'][0]
            maxx = coordinates['boundingbox'][1]
            miny = coordinates['boundingbox'][2]
            maxy = coordinates['boundingbox'][3]

            for item in desiers:
                try:
                    places = requests.get(
                        f"https://api.openrouteservice.org/geocode/search?api_key={API_KEY}&text={item}&sources=openstreetmap,openaddresses,geonames,whosonfirst&boundary.rect.min_lat={minx}&boundary.rect.max_lat={maxx}&boundary.rect.min_lon={miny}&boundary.rect.max_lon={maxy}"
                    ).json()['features']

                    # Code for choosing place 
                    fl = 1
                    for item in places:
                        try:
                            a = item['properties']['street']
                            if (fl == 1):
                                attraction.append([])
                                fl = 0
                            attraction[len(attraction) - 1].append(item)
                            kol += 1
                        except:
                            continue
                except:
                    print("~ ERROR ~")
            print(kol)
            if (kol < 5):
                attractions = 'Извините, произошла какая-то ошибка. Не найдено никаких достопримечаьельностей по вашим предпочтениям.'
                # Updating KB
            else:
                print(attraction)
                kol = 0
                for j in range(0, len(desiers)):
                    for i in range(0, len(attraction)):
                        if (kol <= len(desiers)):
                            try:
                                place = attraction[i][-1]
                                attraction[i].pop(-1)
                                print(place)
                                print()
                                attractions += f"~ {place['properties']['name']}"
                                latCoordString += f"{place['geometry']['coordinates'][0]},"
                                lonCoordString += f"{place['geometry']['coordinates'][1]}," 

                                try:
                                    attractions += f"<p style='opacity: 0.7'>{place['properties']['street']} {place['properties']['housenumber']}</p>"

                                except:
                                    attractions += f"<p style='opacity: 0.7'> - </p>"

                                kol += 1
                            except:
                                continue
                        else:
                            break

                attractions += '<a class="build_map" href="http://c3337100.beget.tech/index.html?x=' + str(coordinates["lon"]) + "&y=" + str(coordinates["lat"]) + "&x=" + latCoordString + "&y=" + lonCoordString + '" style="transition: all .6s ease; display: inline-block; padding: 10px 20px; margin: auto; background: blue; background: #262626; text-decoration: none; border-radius: 10px; color: #538689;">Построить карту</a>'

        except requests.exceptions.ConnectionError:
            self.logger.info(f"FindSomePlacesAgent: finished with connection error")
            return ScResult.ERROR
        
        print(attractions)
        link = create_link(
            str(attractions), ScLinkContentType.STRING, link_type=sc_types.LINK_CONST)
        nrel_format = ScKeynodes.resolve(
                "nrel_format", sc_types.NODE_NOROLE)
        format_html = ScKeynodes.resolve(
                "format_html", sc_types.NODE_CONST)
        format_edge = create_edge(
            sc_types.EDGE_D_COMMON_CONST, link, format_html)
        create_edge(
            sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_format, format_edge)
        
        history_edge = create_edge(
            sc_types.EDGE_D_COMMON_CONST, city_addr, link)
        create_edge(
            sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_attractions, history_edge)
        create_action_answer(action_node, link)
        return ScResult.OK

    def set_unknown_city_link(self, action_node: ScAddr, answer_phrase: ScAddr) -> None:
        unknown_city_link = ScKeynodes.resolve(
            "unknown_city_for_weather_agent_message_text", None)
        if not unknown_city_link.is_valid():
            raise
        create_edge(
            sc_types.EDGE_ACCESS_CONST_POS_PERM, answer_phrase, unknown_city_link)
        create_action_answer(action_node, unknown_city_link)

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
    
    def get_en_idtf(self, entity_addr: ScAddr) -> ScAddr:
        main_idtf = ScKeynodes.resolve(
            "nrel_main_idtf", sc_types.NODE_CONST_NOROLE)
        
        lang_ru = ScKeynodes.resolve("lang_en", sc_types.NODE_CONST_CLASS)

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

    def clear_previous_answer(self, entity, nrel_attractions, answer_phrase):
        message_answer_set = ScSet(set_node=answer_phrase)
        message_answer_set.clear()
        if not entity.is_valid():
            return

        template = ScTemplate()
        template.triple_with_relation(
            entity,
            sc_types.EDGE_D_COMMON_VAR,
            sc_types.LINK,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            nrel_attractions
        )
        search_results = template_search(template)
        for result in search_results:
            delete_edges(result[0], result[2], sc_types.EDGE_D_COMMON_VAR)