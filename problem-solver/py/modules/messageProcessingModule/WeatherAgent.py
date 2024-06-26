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


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class WeatherAgent(ScAgentClassic):
    def __init__(self):
        super().__init__("action_show_weather")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("WeatherAgent finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("WeatherAgent started")

        try:
            message_addr = get_action_arguments(action_node, 1)[0]
            message_type = ScKeynodes.resolve(
                "concept_message_about_weather", sc_types.NODE_CONST_CLASS)

            if not check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, message_type, message_addr):
                self.logger.info(
                    f"WeatherAgent: the message isn't about weather")
                return ScResult.OK

            idtf = ScKeynodes.resolve("nrel_idtf", sc_types.NODE_CONST_NOROLE)
            answer_phrase = ScKeynodes.resolve(
                "show_weather_answer_phrase", sc_types.NODE_CONST_CLASS)
            rrel_city_place = ScKeynodes.resolve("rrel_city_place", sc_types.NODE_ROLE)
            nrel_temperature = ScKeynodes.resolve(
                "nrel_temperature", sc_types.NODE_NOROLE)

            city_addr, country_addr = self.get_entity_addr(
                message_addr, rrel_city_place)

            self.clear_previous_answer(
                city_addr, nrel_temperature, answer_phrase)

            # if there is no such сity in country
            if not country_addr is None:
                if not get_edge(country_addr, city_addr, sc_types.EDGE_D_COMMON_VAR):
                    self.logger.info(f"Country not valid")
                    self.set_unknown_city_link(action_node, answer_phrase)
                    return ScResult.OK
                
            # if there is no such сity
            if not city_addr.is_valid():
                self.logger.info(f"City not valid")
                self.set_unknown_city_link(action_node, answer_phrase)
                return ScResult.OK
            city_idtf_link = self.get_ru_idtf(city_addr)
            answer_city_idtf_link = get_element_by_norole_relation(
                src=city_addr, nrel_node=idtf)
            if not city_idtf_link.is_valid():
                self.logger.info(f"City_idtf not valid")
                self.set_unknown_city_link(action_node, answer_phrase)
                return ScResult.OK
        except:
            self.logger.info(f"WeatherAgent: finished with an error")
            return ScResult.ERROR

        entity_idtf = get_link_content_data(city_idtf_link)
        try:
            temperature = self.get_weather(
                entity_idtf, city_addr, country_addr)
            self.logger.info(f"{temperature}")
        except requests.exceptions.ConnectionError:
            self.logger.info(f"WeatherAgent: finished with connection error")
            return ScResult.ERROR
        link = create_link(
            str(temperature), ScLinkContentType.STRING, link_type=sc_types.LINK_CONST)
        temperature_edge = create_edge(
            sc_types.EDGE_D_COMMON_CONST, city_addr, link)
        create_edge(
            sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_temperature, temperature_edge)
        create_action_answer(action_node, link)

        return ScResult.OK

    def get_weather(self, entity_idtf: ScAddr, city_addr: ScAddr, country_addr: ScAddr) -> float:
        # get entity longitude and latitude
        country_addr = "Belarus"
        if country_addr is not None:
            country = get_link_content_data(self.get_ru_idtf(country_addr))
            coordinates = requests.get(
                f'https://geocode.maps.co/search?city={entity_idtf}&country=Беларусь').json()[0]
        else:
            self.logger.info(f"City none")
            coordinates = requests.get(
                f'https://geocode.maps.co/search?city={entity_idtf}').json()[0]

        # get weather
        BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
        API_KEY = "b2c6abeb0bfa8c28395919438f4eb3d1"
        url = BASE_URL + "appid=" + API_KEY + "&lat=" + str(coordinates['lat']) + '&lon=' + str(coordinates['lon']) + "&lang=ru"
        responce = requests.get(url).json()
        self.logger.info(f"{url}")

        temp = str(round(responce['main']['temp'] - 273.15))
        description = responce['weather'][0]['main']
        name = responce['name']
        img = ''
        if description == 'Clear':
            img = '<div class="weather-image"><svg enable-background="new 0 0 32 32" version="1.1" viewBox="0 0 32 32" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Layer_2"/><g id="Layer_3"/><g id="Layer_4"/><g id="Layer_5"/><g id="Layer_6"/><g id="Layer_7"/><g id="Layer_8"/><g id="Layer_9"/><g id="Layer_10"/><g id="Layer_11"/><g id="Layer_12"/><g id="Layer_13"/><g id="Layer_14"/><g id="Layer_15"/><g id="Layer_16"/><g id="Layer_17"/><g id="Layer_18"/><g id="Layer_19"/><g id="Layer_20"/><g id="Layer_21"><g><path d="M26,16c0,5.5-4.5,10-10,10S6,21.5,6,16S10.5,6,16,6S26,10.5,26,16z" fill="#FFC10A"/></g><g><path d="M16,1c-0.6,0-1,0.4-1,1v2c0,0.6,0.4,1,1,1s1-0.4,1-1V2C17,1.4,16.6,1,16,1z" fill="#F44236"/><path d="M16,27c-0.6,0-1,0.4-1,1v2c0,0.6,0.4,1,1,1s1-0.4,1-1v-2C17,27.4,16.6,27,16,27z" fill="#F44236"/><path d="M30,15h-2c-0.6,0-1,0.4-1,1s0.4,1,1,1h2c0.6,0,1-0.4,1-1S30.6,15,30,15z" fill="#F44236"/><path d="M4,15H2c-0.6,0-1,0.4-1,1s0.4,1,1,1h2c0.6,0,1-0.4,1-1S4.6,15,4,15z" fill="#F44236"/><path d="M25.2,5.4l-1.4,1.4c-0.4,0.4-0.4,1,0,1.4c0.2,0.2,0.5,0.3,0.7,0.3s0.5-0.1,0.7-0.3l1.4-1.4    c0.4-0.4,0.4-1,0-1.4S25.6,5,25.2,5.4z" fill="#F44236"/><path d="M6.8,23.8l-1.4,1.4c-0.4,0.4-0.4,1,0,1.4c0.2,0.2,0.5,0.3,0.7,0.3s0.5-0.1,0.7-0.3l1.4-1.4    c0.4-0.4,0.4-1,0-1.4S7.2,23.4,6.8,23.8z" fill="#F44236"/><path d="M6.8,5.4C6.4,5,5.8,5,5.4,5.4s-0.4,1,0,1.4l1.4,1.4C7,8.4,7.3,8.5,7.5,8.5S8,8.4,8.2,8.2    c0.4-0.4,0.4-1,0-1.4L6.8,5.4z" fill="#F44236"/><path d="M25.2,23.8c-0.4-0.4-1-0.4-1.4,0s-0.4,1,0,1.4l1.4,1.4c0.2,0.2,0.5,0.3,0.7,0.3s0.5-0.1,0.7-0.3    c0.4-0.4,0.4-1,0-1.4L25.2,23.8z" fill="#F44236"/></g></g><g id="Layer_22"/><g id="Layer_23"/><g id="Layer_24"/><g id="Layer_25"/><g id="Wearher"/></svg></div>'
        elif description == 'Clouds':
            img = '<div class="weather-image"><svg enable-background="new 0 0 32 32" version="1.1" viewBox="0 0 32 32" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Layer_2"/><g id="Layer_3"/><g id="Layer_4"/><g id="Layer_5"/><g id="Layer_6"/><g id="Layer_7"/><g id="Layer_8"/><g id="Layer_9"/><g id="Layer_10"/><g id="Layer_11"/><g id="Layer_12"/><g id="Layer_13"/><g id="Layer_14"/><g id="Layer_15"/><g id="Layer_16"/><g id="Layer_17"/><g id="Layer_18"/><g id="Layer_19"/><g id="Layer_20"/><g id="Layer_21"/><g id="Layer_22"/><g id="Layer_23"/><g id="Layer_24"><g><path d="M16.1,9.5c-1.4,0.9-2.4,2.2-2.8,3.7c-0.1,0.3-0.4,0.6-0.7,0.7c-0.1,0-0.2,0-0.2,0c-0.3,0-0.5-0.1-0.7-0.3    C10.7,12.5,9.4,12,8,12c-1.2,0-2.3,0.4-3.2,1.1c-0.3,0.2-0.6,0.3-1,0.2c-0.3-0.1-0.6-0.4-0.7-0.7C3.1,12.1,3,11.5,3,11    c0-3.9,3.1-7,7-7c2.8,0,5.3,1.7,6.5,4.3C16.6,8.7,16.5,9.2,16.1,9.5z" fill="#FFC10A"/></g><g><path d="M31,15c0,5-4.5,9-10,9H8c-3.9,0-7-3.1-7-7c0-2.1,0.9-4,2.5-5.4C4.8,10.6,6.4,10,8,10    c1.4,0,2.8,0.4,3.9,1.2c0.7-1.3,1.7-2.5,3-3.4C16.7,6.6,18.8,6,21,6C26.5,6,31,10,31,15z" fill="#ffffff"/></g></g><g id="Layer_25"/><g id="Wearher"/></svg></div>'
        elif description == 'Rain':
            img = '<div class="weather-image"><svg enable-background="new 0 0 32 32" version="1.1" viewBox="0 0 32 32" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Layer_2"/><g id="Layer_3"/><g id="Layer_4"/><g id="Layer_5"/><g id="Layer_6"/><g id="Layer_7"/><g id="Layer_8"/><g id="Layer_9"/><g id="Layer_10"/><g id="Layer_11"/><g id="Layer_12"/><g id="Layer_13"/><g id="Layer_14"/><g id="Layer_15"/><g id="Layer_16"/><g id="Layer_17"/><g id="Layer_18"/><g id="Layer_19"/><g id="Layer_20"/><g id="Layer_21"/><g id="Layer_22"><g><path d="M16.5,22.1c-0.5-0.3-1.1-0.1-1.4,0.4l-1.2,2.2c-0.3,0.5-0.1,1.1,0.4,1.4c0.2,0.1,0.3,0.1,0.5,0.1    c0.3,0,0.7-0.2,0.9-0.5l1.2-2.2C17.1,23,17,22.4,16.5,22.1z" fill="#16BCD4"/><path d="M13.7,27c-0.5-0.3-1.1-0.1-1.4,0.4l-1.2,2.2c-0.3,0.5-0.1,1.1,0.4,1.4C11.7,31,11.8,31,12,31    c0.3,0,0.7-0.2,0.9-0.5l1.2-2.2C14.4,27.8,14.2,27.2,13.7,27z" fill="#16BCD4"/><path d="M10.5,22.1C10,21.9,9.4,22,9.1,22.5l-1.2,2.2c-0.3,0.5-0.1,1.1,0.4,1.4c0.2,0.1,0.3,0.1,0.5,0.1    c0.3,0,0.7-0.2,0.9-0.5l1.2-2.2C11.1,23,11,22.4,10.5,22.1z" fill="#16BCD4"/><path d="M7.7,27c-0.5-0.3-1.1-0.1-1.4,0.4l-1.2,2.2C4.9,30,5,30.6,5.5,30.9C5.7,31,5.8,31,6,31    c0.3,0,0.7-0.2,0.9-0.5l1.2-2.2C8.4,27.8,8.2,27.2,7.7,27z" fill="#16BCD4"/><path d="M22.5,22.1c-0.5-0.3-1.1-0.1-1.4,0.4l-1.2,2.2c-0.3,0.5-0.1,1.1,0.4,1.4c0.2,0.1,0.3,0.1,0.5,0.1    c0.3,0,0.7-0.2,0.9-0.5l1.2-2.2C23.1,23,23,22.4,22.5,22.1z" fill="#16BCD4"/><path d="M19.7,27c-0.5-0.3-1.1-0.1-1.4,0.4l-1.2,2.2c-0.3,0.5-0.1,1.1,0.4,1.4C17.7,31,17.8,31,18,31    c0.3,0,0.7-0.2,0.9-0.5l1.2-2.2C20.4,27.8,20.2,27.2,19.7,27z" fill="#16BCD4"/></g><g><path d="M31,15c0,5-4.5,9-10,9H8c-3.9,0-7-3.1-7-7s3.1-7,7-7c1.4,0,2.8,0.4,3.9,1.2C13.5,8.1,17.1,6,21,6    C26.5,6,31,10,31,15z" fill="#ffffff"/></g></g><g id="Layer_23"/><g id="Layer_24"/><g id="Layer_25"/><g id="Wearher"/></svg></div>'
        elif description == 'Drizzle' or description == "Snow":
            img = '<div class="weather-image"><svg enable-background="new 0 0 32 32" version="1.1" viewBox="0 0 32 32" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Layer_2"/><g id="Layer_3"/><g id="Layer_4"/><g id="Layer_5"/><g id="Layer_6"/><g id="Layer_7"/><g id="Layer_8"/><g id="Layer_9"/><g id="Layer_10"/><g id="Layer_11"/><g id="Layer_12"/><g id="Layer_13"/><g id="Layer_14"/><g id="Layer_15"/><g id="Layer_16"/><g id="Layer_17"/><g id="Layer_18"/><g id="Layer_19"/><g id="Layer_20"><path d="M30,15H17V2c0-0.6-0.4-1-1-1s-1,0.4-1,1v13H2c-0.6,0-1,0.4-1,1s0.4,1,1,1h13v13c0,0.6,0.4,1,1,1s1-0.4,1-1   V17h13c0.6,0,1-0.4,1-1S30.6,15,30,15z" fill="#2197F3"/><g><path d="M16,11c-0.2,0-0.4-0.1-0.6-0.2l-5-4c-0.4-0.3-0.5-1-0.2-1.4c0.3-0.4,1-0.5,1.4-0.2L16,8.7l4.4-3.5    c0.4-0.3,1.1-0.3,1.4,0.2c0.3,0.4,0.3,1.1-0.2,1.4l-5,4C16.4,10.9,16.2,11,16,11z" fill="#16BCD4"/></g><g><path d="M21,27c-0.2,0-0.4-0.1-0.6-0.2L16,23.3l-4.4,3.5c-0.4,0.3-1.1,0.3-1.4-0.2c-0.3-0.4-0.3-1.1,0.2-1.4l5-4    c0.4-0.3,0.9-0.3,1.2,0l5,4c0.4,0.3,0.5,1,0.2,1.4C21.6,26.9,21.3,27,21,27z" fill="#16BCD4"/></g><g><path d="M6,22c-0.2,0-0.4-0.1-0.6-0.2c-0.4-0.3-0.5-1-0.2-1.4L8.7,16l-3.5-4.4c-0.3-0.4-0.3-1.1,0.2-1.4    c0.4-0.3,1.1-0.3,1.4,0.2l4,5c0.3,0.4,0.3,0.9,0,1.2l-4,5C6.6,21.9,6.3,22,6,22z" fill="#16BCD4"/></g><g><path d="M26,22c-0.3,0-0.6-0.1-0.8-0.4l-4-5c-0.3-0.4-0.3-0.9,0-1.2l4-5c0.3-0.4,1-0.5,1.4-0.2    c0.4,0.3,0.5,1,0.2,1.4L23.3,16l3.5,4.4c0.3,0.4,0.3,1.1-0.2,1.4C26.4,21.9,26.2,22,26,22z" fill="#16BCD4"/></g></g><g id="Layer_21"/><g id="Layer_22"/><g id="Layer_23"/><g id="Layer_24"/><g id="Layer_25"/><g id="Wearher"/></svg></div>'
        elif description == 'Thunderstorm':
            img = '<div class="weather-image"><svg enable-background="new 0 0 32 32" version="1.1" viewBox="0 0 32 32" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Layer_2"/><g id="Layer_3"/><g id="Layer_4"/><g id="Layer_5"/><g id="Layer_6"/><g id="Layer_7"/><g id="Layer_8"/><g id="Layer_9"/><g id="Layer_10"/><g id="Layer_11"/><g id="Layer_12"/><g id="Layer_13"/><g id="Layer_14"/><g id="Layer_15"/><g id="Layer_16"><g><path d="M31,15c0,4.4-3.5,8.1-8.3,8.9c0,0-0.1,0-0.1,0L19.7,24H8c-3.9,0-7-3.1-7-7s3.1-7,7-7    c1.4,0,2.8,0.4,3.9,1.2C13.5,8.1,17.1,6,21,6C26.5,6,31,10,31,15z" fill="#ffffff"/></g><g><path d="M26.9,16.9l-7.2,13.6c-0.2,0.3-0.5,0.5-0.9,0.5c-0.1,0-0.2,0-0.3,0c-0.5-0.1-0.8-0.6-0.7-1.1l1.1-8.9H14    c-0.4,0-0.7-0.2-0.9-0.5c-0.2-0.3-0.2-0.7,0-1l6-10c0.2-0.4,0.7-0.6,1.1-0.5c0.4,0.1,0.7,0.5,0.7,1v5.4h5c0.3,0,0.7,0.2,0.9,0.5    S27,16.6,26.9,16.9z" fill="#FFC10A"/></g></g><g id="Layer_17"/><g id="Layer_18"/><g id="Layer_19"/><g id="Layer_20"/><g id="Layer_21"/><g id="Layer_22"/><g id="Layer_23"/><g id="Layer_24"/><g id="Layer_25"/><g id="Wearher"/></svg></div>'
        else:
            img = '<div class="weather-image"><svg enable-background="new 0 0 32 32" version="1.1" viewBox="0 0 32 32" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Layer_2"/><g id="Layer_3"/><g id="Layer_4"/><g id="Layer_5"/><g id="Layer_6"/><g id="Layer_7"/><g id="Layer_8"/><g id="Layer_9"/><g id="Layer_10"/><g id="Layer_11"/><g id="Layer_12"><g><path d="M24,13H8c-0.6,0-1,0.4-1,1s0.4,1,1,1h16c0.6,0,1-0.4,1-1S24.6,13,24,13z" fill="#2197F3"/><path d="M19,18c0-0.6-0.4-1-1-1H6c-0.6,0-1,0.4-1,1s0.4,1,1,1h12C18.6,19,19,18.6,19,18z" fill="#2197F3"/><path d="M21,21H9c-0.6,0-1,0.4-1,1s0.4,1,1,1h12c0.6,0,1-0.4,1-1S21.6,21,21,21z" fill="#2197F3"/><path d="M20,25h-8c-0.6,0-1,0.4-1,1s0.4,1,1,1h8c0.6,0,1-0.4,1-1S20.6,25,20,25z" fill="#2197F3"/><path d="M18,29h-4c-0.6,0-1,0.4-1,1s0.4,1,1,1h4c0.6,0,1-0.4,1-1S18.6,29,18,29z" fill="#2197F3"/><path d="M28,1H2C1.4,1,1,1.4,1,2s0.4,1,1,1h26c0.6,0,1,0.4,1,1s-0.4,1-1,1H6C4.3,5,3,6.3,3,8s1.3,3,3,3h20    c0.6,0,1-0.4,1-1s-0.4-1-1-1H6C5.4,9,5,8.6,5,8s0.4-1,1-1h22c1.7,0,3-1.3,3-3S29.7,1,28,1z" fill="#2197F3"/></g></g><g id="Layer_13"/><g id="Layer_14"/><g id="Layer_15"/><g id="Layer_16"/><g id="Layer_17"/><g id="Layer_18"/><g id="Layer_19"/><g id="Layer_20"/><g id="Layer_21"/><g id="Layer_22"/><g id="Layer_23"/><g id="Layer_24"/><g id="Layer_25"/><g id="Wearher"/></svg></div>'
        
        temperat = f'<div class="weather_wrapper" data-speed="1"><p style="text-align: center; margin-top: 10px;">{name}</p>{img}<p class="temperature" style="text-align: center; position: relative; top: -15px; font-size: 30px !important;">{temp}°C</p></div>'

        self.logger.info(
            f"WeatherAgent: The temperature in {get_system_idtf(city_addr)} is {temp}°C: {description}")
        return temperat

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

    def get_entity_addr(self, message_addr: ScAddr, rrel_entity: ScAddr):
        rrel_entity = ScKeynodes.resolve("rrel_city_place", sc_types.NODE_ROLE)
        concept_country = ScKeynodes.resolve(
            "concept_country", sc_types.NODE_CONST_CLASS)
        template = ScTemplate()
        # entity node or link
        template.triple_with_relation(
            message_addr,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            sc_types.VAR,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            rrel_entity,
        )
        search_results = template_search(template)
        if len(search_results) == 0:
            return ScAddr(0), None
        entity = search_results[0][2]
        if len(search_results) == 1:
            return entity, None
        # check country position in search_results
        country_edge = get_edge(
            concept_country, entity, sc_types.EDGE_ACCESS_VAR_POS_PERM)
        if country_edge:
            return search_results[1][2], entity
        else:
            return entity, search_results[1][2]

    def clear_previous_answer(self, entity, nrel_temperature, answer_phrase):
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
            nrel_temperature
        )
        search_results = template_search(template)
        for result in search_results:
            delete_edges(result[0], result[2], sc_types.EDGE_D_COMMON_VAR)
