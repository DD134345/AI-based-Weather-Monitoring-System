import React from 'react';
import ReactDOM from 'react-dom';
import App from './app';

ReactDOM.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
    document.getElementById('root') // Ensure this matches the id in index.html
);