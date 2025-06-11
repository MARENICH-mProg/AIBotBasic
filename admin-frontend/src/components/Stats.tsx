import React, { useEffect, useState } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { PeopleAlt, Message, SentimentVerySatisfied } from '@mui/icons-material';

interface StatsData {
  total_users: number;
  active_users_today: number;
  total_messages: number;
  funny_messages: number;
}

const Stats: React.FC = () => {
  const [stats, setStats] = useState<StatsData | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/stats')
      .then(response => response.json())
      .then(data => setStats(data))
      .catch(error => console.error('Error fetching stats:', error));
  }, []);

  if (!stats) return <Typography>Загрузка статистики...</Typography>;

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
      <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <PeopleAlt color="primary" />
        <div>
          <Typography variant="h6">{stats.total_users}</Typography>
          <Typography variant="body2">Всего пользователей</Typography>
        </div>
      </Paper>
      <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <PeopleAlt color="secondary" />
        <div>
          <Typography variant="h6">{stats.active_users_today}</Typography>
          <Typography variant="body2">Активных сегодня</Typography>
        </div>
      </Paper>
      <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Message color="primary" />
        <div>
          <Typography variant="h6">{stats.total_messages}</Typography>
          <Typography variant="body2">Всего сообщений</Typography>
        </div>
      </Paper>
      <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <SentimentVerySatisfied color="secondary" />
        <div>
          <Typography variant="h6">{stats.funny_messages}</Typography>
          <Typography variant="body2">Смешных сообщений</Typography>
        </div>
      </Paper>
    </Box>
  );
};

export default Stats; 