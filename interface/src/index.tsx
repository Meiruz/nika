import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { createGlobalStyle } from 'styled-components';

import { store } from '@store';

import { App } from './App';

const GlobalStyle = createGlobalStyle`
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700;800&display=swap');
  body {
    margin: 0;
    display: flex;
    font-family: 'Montserrat', sans-serif;
    /* For firefox full height */
    height: 100%;
    background: #101514;
    padding: 0;
    overflow: hidden;
  }
  #content {
    flex-grow: 1;
    display: flex;
  }
  * {
    box-sizing: border-box;
  }

  @-webkit-keyframes zoomIn {
    from {
      opacity: 0;
      -webkit-transform: scale3d(0.3, 0.3, 0.3);
      transform: scale3d(0.3, 0.3, 0.3);
    }
  
    50% {
      opacity: 1;
    }
  }
`;

ReactDOM.render(
    <Provider store={store}>
        <BrowserRouter>
            <GlobalStyle />
            <App />
        </BrowserRouter>
    </Provider>,
    document.getElementById('content'),
);
