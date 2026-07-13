const express = require('express');
const app = express();
const PORT = 3000;

app.get('/', (req, res) => {
    res.send('¡Hola! Estás conectado al servidor de mi PC.');
});

// ESCUCHAR EN CUALQUIER RED (0.0.0.0)
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Servidor de la PC activo en el puerto ${PORT}`);
});
