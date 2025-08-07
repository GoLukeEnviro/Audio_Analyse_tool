import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Paper, Typography, Box } from '@mui/material';
import { useTheme } from '@mui/material/styles';

interface EnergyChartProps {
  data: {
    energy_value: number[];
    timestamps: number[];
  };
  title?: string;
  height?: number;
}

const EnergyChart: React.FC<EnergyChartProps> = ({ 
  data, 
  title = "Energie-Verlauf", 
  height = 300 
}) => {
  const theme = useTheme();

  // Transform data for recharts
  const chartData = data.energy_value.map((energy, index) => ({
    time: data.timestamps[index],
    energy: energy,
    timeFormatted: `${Math.floor(data.timestamps[index] / 60)}:${(data.timestamps[index] % 60).toString().padStart(2, '0')}`
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Paper sx={{ p: 1.5, backgroundColor: 'background.paper', border: 1, borderColor: 'divider' }}>
          <Typography variant="body2">
            Zeit: {data.timeFormatted}
          </Typography>
          <Typography variant="body2" color="primary">
            Energie: {(data.energy * 100).toFixed(1)}%
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Box sx={{ width: '100%', height: height }}>
        <ResponsiveContainer>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke={theme.palette.divider}
            />
            <XAxis 
              dataKey="timeFormatted"
              stroke={theme.palette.text.secondary}
              fontSize={12}
            />
            <YAxis 
              domain={[0, 1]}
              tickFormatter={(value) => `${Math.round(value * 100)}%`}
              stroke={theme.palette.text.secondary}
              fontSize={12}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="energy" 
              stroke={theme.palette.primary.main}
              strokeWidth={2}
              dot={{ fill: theme.palette.primary.main, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: theme.palette.primary.main, strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
};

export default EnergyChart;