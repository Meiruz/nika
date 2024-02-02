import React, { useEffect, useState, useReducer, ChangeEvent } from 'react';
import { WrapperSettings, Container, Setting, SettingsText, SaveSettings } from './styled';
import { client } from '@api';
import { routes } from '@constants';
import { ScAddr, ScConstruction, ScLinkContent, ScLinkContentType } from 'ts-sc-client';
import { ScTemplate, ScType } from 'ts-sc-client';
import { Redirect } from 'react-router';
import { checkUser } from '@api/sc/checkUser';
import Cookie from 'universal-cookie';
import { getUserName, findSettings, updateSettings } from '@api/sc/checkUser';

export const Profile = () => {
    // Get Cookies
    const cookie = new Cookie();
    const userAddr = cookie.get('userAddr') ? new ScAddr(parseInt(String(cookie.get('userAddr')))) : new ScAddr(0);
    const password = cookie.get('password');

    const [settingTheme, setSettingTheme] = useState<string>('');
    const [settingFontSize, setSettingFontSize] = useState<string>('');
    const [settingAccentColor, setSettingAccentColor] = useState<string>('');
    const [settingLang, setSettingLang] = useState<string>('');
    const [settingInvalideMode, setSettingInvalideMode] = useState<string>('');

    useEffect(() => {
        (async () => {
            const defaultTheme = String(await findSettings(userAddr, 'nrel_theme'));
            setSettingTheme(defaultTheme);

            const defaultFontSize = String(await findSettings(userAddr, 'nrel_font_size'));
            setSettingFontSize(defaultFontSize);

            const defaultAccentColor = await String(findSettings(userAddr, 'nrel_accent_color'));
            setSettingAccentColor(defaultAccentColor);

            const defaultLang = String(await findSettings(userAddr, 'nrel_lang'));
            setSettingLang(defaultLang);

            const defaultInvalideMode = String(await findSettings(userAddr, 'nrel_invalid'));
            setSettingInvalideMode(defaultInvalideMode);
        })();
    }, []);

    const [savedSettings, setSavedSettings] = useState<boolean>(false);

    const changeTheme = (e: ChangeEvent<HTMLSelectElement>) => {
        setSettingTheme(e.target.value);
    };

    const changeFontSize = (e: ChangeEvent<HTMLSelectElement>) => {
        setSettingFontSize(e.target.value);
    };

    const changeAccentColor = (e: ChangeEvent<HTMLInputElement>) => {
        setSettingAccentColor(e.target.value);
    };

    const changeLang = (e: ChangeEvent<HTMLSelectElement>) => {
        setSettingLang(e.target.value);
    };

    const changeInvalideMode = (e: ChangeEvent<HTMLInputElement>) => {
        setSettingInvalideMode(e.target.checked ? 'on' : 'off');
    };

    const saveSettings = () => {
        console.log(1);
        updateSettings(userAddr, 'nrel_theme', settingTheme);
    };

    return (
        <>
            {savedSettings ? <Redirect to={{ pathname: routes.HOME }} /> : ''}

            <Container>
                <SettingsText>Настройки профиля</SettingsText>
                <WrapperSettings>
                    <Setting>
                        <p>Тема</p>
                        <select onChange={(e) => changeTheme(e)} value={settingTheme}>
                            <option value="dark">Темная</option>
                            <option value="light">Светлая</option>
                        </select>
                    </Setting>
                    <Setting>
                        <p>Размер текста</p>
                        <select onChange={(e) => changeFontSize(e)} value={settingFontSize}>
                            <option value="small">Мелкий</option>
                            <option value="medium">Средний</option>
                            <option value="big">Большой</option>
                        </select>
                    </Setting>
                    <Setting>
                        <p>Цвет интерфейса</p>
                        <input type="color" onChange={(e) => changeAccentColor(e)} value={settingAccentColor} />
                    </Setting>
                    <Setting>
                        <p>Язык</p>
                        <select onChange={(e) => changeLang(e)} value={settingLang}>
                            <option value="ru">Русский</option>
                            <option value="en">Английский</option>
                        </select>
                    </Setting>
                    <Setting>
                        <p>Режим для людей с ограниченными возможностями</p>
                        <input
                            type="checkbox"
                            onChange={(e) => changeInvalideMode(e)}
                            checked={settingInvalideMode == 'on' ? true : false}
                        />
                    </Setting>
                    <SaveSettings onClick={saveSettings}>Сохранить</SaveSettings>
                </WrapperSettings>
            </Container>
        </>
    );
};