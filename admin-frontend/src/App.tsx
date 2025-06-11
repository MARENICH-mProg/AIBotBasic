import React from 'react';
import { Container, Box, Typography, CssBaseline, AppBar, Toolbar } from '@mui/material';
import Stats from './components/Stats';
import Messages from './components/Messages';

function App() {
  return (
    <>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6">
            Админ-панель Telegram бота
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg">
        <Box sx={{ mt: 4, mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Статистика
          </Typography>
          <Stats />
          
          <Typography variant="h4" component="h1" sx={{ mt: 4 }} gutterBottom>
            Сообщения
          </Typography>
          <Messages />
        </Box>
      </Container>
    </>
  );
}

export default App;
