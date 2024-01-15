import styled from 'styled-components';
import { ChatPageWrapper } from '@components/ChatPageWrapper';

export const Wrapper = styled(ChatPageWrapper)`
    display: block;
`;

export const ChatWrapper = styled.div`
    grid-area: chat;
`;

export const DesireButton = styled.button`
    position: relative;
    width: 49%;
    margin: 5px 0;
    cursor: pointer;
    border: none;
    height: 150px;
    border-radius: 40px;
    overflow: hidden;
    &hover {
        opacity: 0.4;
    }
`;

export const SaveButton = styled.button`
    padding: 10px 15px;
    border: none;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 900;
    color: white;
    cursor: pointer;
    background-color: #538689;
    &hover {
        background-color: #47969a;
    }
`;

export const NameInput = styled.input`
    width: 100%;
    background: #333436;
    border-radius: 15px;
    border: none;
    padding: 15px;
    outline: none;
    color: white;
    font-weight: 800;
    font-size: 16px;
`;

export const IntroWrapper = styled.div`
    position: relative;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    backdrop-filter: blur(100px);
`;

export const BackgroundCircle = styled.div`
    position: absolute;
    top: -20%;
    right: -15%;
    height: 80vmin;
    width: 80vmin;
    border-radius: 50%;
    background: #538689;
`;

export const WrapperContentIntro = styled.div`
    color: white;
    text-align: center;
    max-width: 500px;
    margin: auto;
    padding: 5px;
`;

export const HelloTextIntro = styled.h2`
    font-weight: 900;
    color: white;
    font-size: 30px;
    margin-bottom: 10px;
    margin: 80px 0 20px 0;
`;

export const MainBtnsIntro = styled.h2`
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 1%;
    margin: 10px 0;
`;

export const LinerBtns = styled.div`
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
    background: linear-gradient(180deg, rgba(52,91,102,0) 0%, rgba(0,0,0,1) 91%); 
`;

export const TextButton = styled.div`
    position: absolute;
    bottom: 10px;
    left: 50%;
    color: white;
    font-size: 0.8em;
    font-weight: 800;
    z-index: 10;
    transform: translate(-50%, 0);
`;

export const SelectMask = styled.div`
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
    backdrop-filter: blur(100px);
`; 