import { CandlesService } from "../client";
import { useRef, useState, useEffect } from "react";
import { createChart, IChartApi } from "lightweight-charts";


const Test = () => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const [candles, setCandles] = useState([]);
    const [exchange, setExchange] = useState("alpaca");
    const [symbol, setSymbol] = useState("AAPL");

    const fetchCandles = async (exchange: string, symbol: string, startTime: Date, endTime: Date) => {
        const response = CandlesService.getCandlesCandlesExchangeSymbolGet({
            exchange: exchange,
            symbol: symbol,
            startTime: startTime.toISOString(),
            endTime: endTime.toISOString(),
        });
        const data = await response;
        return data;
    };

    const loadInitialCandles = async () => {
        const startTime = new Date();
        startTime.setDate(startTime.getDate() - 30); // Default: past 30 days
        const endTime = new Date();
    
        const data = await fetchCandles(exchange, symbol, startTime, endTime);
        setCandles(data);
    
        if (chartRef.current) {
          const candleSeries = chartRef.current.addCandlestickSeries();
          candleSeries.setData(
            data.map((candle) => ({
              time: candle.time,
              open: candle.open,
              high: candle.high,
              low: candle.low,
              close: candle.close,
            }))
          );
    
          chartRef.current.timeScale().fitContent();
    
          // Add listener for visible range changes
          chartRef.current.timeScale().subscribeVisibleTimeRangeChange((visibleRange) => {
            if (visibleRange) {
              handleVisibleRangeChange(visibleRange);
            }
          });
        }
      };

    const handleVisibleRangeChange = async (visibleRange: { from: number; to: number }) => {
        const startTime = new Date(visibleRange.from * 1000); // Convert seconds to milliseconds
        const endTime = new Date(visibleRange.to * 1000);
    
        const data = await fetchCandles(exchange, symbol, startTime, endTime);
        setCandles((prevCandles) => {
          // Merge new data with existing data to avoid overwriting
          const merged = [...prevCandles];
          data.forEach((candle) => {
            if (!merged.some((existing) => existing.time === candle.time)) {
              merged.push(candle);
            }
          });
          return merged.sort((a, b) => a.time - b.time);
        });
    };

    useEffect(() => {
        if (!chartContainerRef.current) return;
    
        const chart = createChart(chartContainerRef.current, {
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
          layout: {
            textColor: "white",
            backgroundColor: "#000",
          },
        });
        chartRef.current = chart;
    
        loadInitialCandles();
    
        return () => {
          chart.remove();
          chartRef.current = null;
        };
    }, [exchange, symbol]);
  
    return (
        <div className="App" style={{ width: "100vw", height: "100vh" }}>
          <div>
            <label>
              Exchange:
              <input
                type="text"
                value={exchange}
                onChange={(e) => setExchange(e.target.value)}
              />
            </label>
            <label>
              Symbol:
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
              />
            </label>
            <button onClick={loadInitialCandles}>Load Candles</button>
          </div>
          <div
            ref={chartContainerRef}
            style={{ position: "relative", width: "100%", height: "80%" }}
          />
        </div>
    );
};

export default Test;
