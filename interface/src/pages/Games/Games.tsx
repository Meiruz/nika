import React, { useEffect, useState, useReducer, ChangeEvent } from 'react';
import { Wrapper, Container, GameLink, NavLink, Arrow, Linktitle } from './styled';
import { client } from '@api';
import { routes } from '@constants';
import { ScAddr, ScConstruction, ScLinkContent, ScLinkContentType } from 'ts-sc-client';
import { ScTemplate, ScType, ScEventType } from 'ts-sc-client';
import { Redirect } from 'react-router';
import { checkUser, getFontSizeFromSettings, getUserName, getUserSettings, translateWord } from '@api/sc/checkUser';
import Cookie from 'universal-cookie';
import styled from 'styled-components';

export const Saved = () => {
    // Get Cookies
    const cookie = new Cookie();
    const cookieUserAddr = cookie.get('userAddr')
        ? new ScAddr(parseInt(String(cookie.get('userAddr'))))
        : new ScAddr(0);
    const cookiePassword = cookie.get('password');

    const [redirectError, setRedirectError] = useState<boolean | undefined>(undefined);
    const [noDesireError, setNoDesireError] = useState<boolean | undefined>(undefined);
    const [userName, setUserName] = useState<string | undefined>(undefined);
    const [userTheme, setUserTheme] = useState<String>('dark');

    const [accentColor, setAccentColor] = useState<string | undefined>('black');
    const [params, setParams] = useState<{}>({});

    const check = async () => {
        if (cookieUserAddr.isValid() && cookiePassword) {
            const name = await getUserName(cookieUserAddr);
            if (!(await checkUser(cookieUserAddr, cookiePassword))) {
                setRedirectError(true);
                return;
            } else if (!name) {
                setNoDesireError(true);
                return;
            } else {
                setUserName(name);
            }
        } else setRedirectError(true);
    };

    useEffect(() => {
        (async () => {
            check();

            const userSettings = await getUserSettings(cookieUserAddr);
            setParams(userSettings);
            setAccentColor(userSettings['nrel_accent_color']);
            setUserTheme(userSettings['nrel_theme']);
        })();
    }, []);

    return (
        <>
            <NavLink href={routes.HOME} style={{ background: '#413d3d' }} className="nav">
                <Arrow></Arrow>
                <Linktitle className="title">{translateWord('Назад', params['nrel_lang'])}</Linktitle>
            </NavLink>
            <Wrapper>
                <Container>
                    <h2
                        style={{
                            color: 'white',
                            fontWeight: '900',
                            fontSize: getFontSizeFromSettings(params['nrel_font_size']),
                        }}
                    >
                        {translateWord('Развлечения', params['nrel_lang'])}
                    </h2>

                    <p>1. Wordlie</p>
                    <GameLink href="https://wordlegame.org/ru">
                        <img src="https://cdn.apartmenttherapy.info/image/upload/v1697122988/at/art/design/2023-10/ApartmentTherapy_Wordle_Final.jpg" />
                    </GameLink>

                    <br />

                    <p>2. Solitare</p>
                    <GameLink href="https://solitaire.online/">
                        <img src="https://www.usatoday.com/gcdn/presto/2023/01/13/USAT/5f20d01f-a206-48b5-a5e3-2740279e498d-Solitaire-topper-2.png?crop=3799,1876,x1,y677&width=1440&height=711&format=pjpg&auto=webp&quality=60" />
                    </GameLink>
                </Container>
            </Wrapper>
        </>
    );
};
