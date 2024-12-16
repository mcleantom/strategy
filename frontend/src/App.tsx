import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import './App.css';

function App() {
  const chartContainerRef = useRef(null);

  useEffect(() => {
    if (chartContainerRef.current === null) { 
      return;
    }
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        attributionLogo: false
      }
    });

    const lineSeries = chart.addLineSeries();

    const data = [
      { time: 1640995200, value: 71 },
      { time: 1641081600, value: 68 },
      { time: 1641168000, value: 75 },
      { time: 1641254400, value: 78 },
      { time: 1641340800, value: 80 },
    ];

    lineSeries.setData(data);

    return () => {
      chart.remove();
    };
  }, []);

  return (
    <div className="App">
      <div ref={chartContainerRef} style={{ position: 'relative', width: '500px', height: '200px' }} />
    </div>
  );
}

export default App;
