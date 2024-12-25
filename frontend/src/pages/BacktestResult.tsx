import { Card, Center, Container, Heading, HStack, Spinner, Text } from "@chakra-ui/react";
import {
  Box,
  VStack,
} from "@chakra-ui/react";
import { createChart } from "lightweight-charts";
import { useEffect, useRef, useState } from "react";
import { BacktestService, BacktestResult } from "@/client";
import { Navbar } from "@/components/navbar";
import { useParams } from "react-router-dom";


const EquityChart = ({backtestedResult} : {backtestedResult: BacktestResult}) => {
    const chartContainerRef = useRef<HTMLDivElement | null>(null);
    
    useEffect(() => {
        if (chartContainerRef.current === null || backtestedResult === null || chartContainerRef == null) { 
            return;
        }
      const chart = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth,
        height: 300,
        timeScale: {
            minBarSpacing: 0.0005,
        }
      });
  
      const lineSeries = chart.addLineSeries();
      const data = backtestedResult.equity_curve
        .map((item) => ({
            time: item.unix_seconds,
            value: item.value
        }))
      lineSeries.setData(data);

      const baselineSeries = chart.addLineSeries({
        color: 'red',
        lineWidth: 2,
      });
      const baselineCurveData = backtestedResult.baseline
        .map((item) => ({
          time: item.unix_seconds,
          value: item.close,
        }));
      baselineSeries.setData(baselineCurveData);
    
      // Resize chart on window resize
      const handleResize = () => {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      };
  
      window.addEventListener("resize", handleResize);
      chart.timeScale().fitContent();
      return () => {
        window.removeEventListener("resize", handleResize);
        chart.remove();
      };
    }, [backtestedResult]);
  
    return <Box ref={chartContainerRef} width="100%" />;
};
  

const Metric: React.FC<{ label: string; value: string | number }> = ({ label, value }) => {
  value = typeof value === "number"
  ? Number.isInteger(value)
    ? value.toFixed(0) // No decimal places for integers
    : value.toFixed(2) // Two decimal places for floating-point numbers
  : value;
  
  return (
      <HStack justify="space-between" width="100%">
        <Text>{label}:</Text>
        <Text>{value}</Text>
      </HStack>
    );
};

const BacktestResultComponent = () => {
  const { backtestId } = useParams();
  const [backtestedResult, setBacktestedResult] = useState<BacktestResult | null>(null);
      
  useEffect(() => {
    if (!backtestId) {
      return;
    }
    BacktestService.getBacktestResultBacktestsBacktestIdGet({
      backtestId: Number(backtestId)
    })
      .then((result) => {
        setBacktestedResult(result);
      })
      .catch((error) => {
        console.error('Error fetching backtest result:', error);
      });
  }, []);

  if (!backtestedResult) {
    return (
      <Box>
        <Navbar/>
        <Container>
          <Center>
            <Spinner size="sm"/>
          </Center>
        </Container>
      </Box>
      
    )
  }

  return (
    <Box>
      <Navbar />
      <Container>
          <Box p={4}>
              <Card.Root>
                  <Card.Header><Heading size="md">Equity Curve</Heading></Card.Header>
                  <Card.Body>
                    {
                      backtestedResult ? <EquityChart backtestedResult={backtestedResult}/> : <></>
                    }
                  </Card.Body>
              </Card.Root>
              <HStack flexDirection={{ base: "column", md: "row" }} pt={4} gap="4" justify="center" width="100%" alignItems={"flex-start"}>
                  <Card.Root width="full">
                      <Card.Header><Heading size="md">Performance Metrics</Heading></Card.Header>
                      <Card.Body>
                          <VStack align="start" gap={2}>
                          <Metric label="PNL" value="3919.60 (39.20%)" />
                          <Metric label="Win rate" value="48.57%" />
                          <Metric label="Sharpe ratio" value={backtestedResult.performance_metrics.sharpe_ratio} />
                          <Metric label="mdart Sharpe" value={backtestedResult.performance_metrics.mdart_sharpe} />
                          <Metric label="Sortino ratio" value={0} />
                          <Metric label="mdart Sortino" value={backtestedResult.performance_metrics.mdart_sharpe} />
                          <Metric label="Calmar ratio" value={backtestedResult.performance_metrics.calmar_ratio} />
                          <Metric label="Omega ratio" value={backtestedResult.performance_metrics.omega_ratio} />
                          <Metric label="Serenity index" value={backtestedResult.performance_metrics.serenity_index} />
                          <Metric label="Average win/loss" value={backtestedResult.performance_metrics.average_win_loss} />
                          <Metric label="Average win" value={backtestedResult.performance_metrics.average_win} />
                          <Metric label="Average loss" value={backtestedResult.performance_metrics.average_loss} />
                          </VStack>
                      </Card.Body>
                  </Card.Root>

                  <Card.Root width="full">
                      <Card.Header><Heading size="md">Risk Metrics</Heading></Card.Header>
                      <Card.Body>
                          <VStack align="start" gap={2}>
                          <Metric label="Total losing streak" value={backtestedResult.risk_metrics.total_losing_streak} />
                          <Metric label="Largest losing trade" value={backtestedResult.risk_metrics.largest_losing_trade} />
                          <Metric label="Largest winning trade" value={backtestedResult.risk_metrics.largest_winning_trade} />
                          <Metric label="Total winning streak" value={backtestedResult.risk_metrics.total_winning_streak} />
                          <Metric label="Current streak" value="1" />
                          <Metric label="Expectancy" value={backtestedResult.risk_metrics.expectancy} />
                          <Metric label="Expected net profit" value={backtestedResult.risk_metrics.expected_net_profit} />
                          <Metric label="Average holding period" value={backtestedResult.risk_metrics.average_holding_period} />
                          <Metric label="Gross profit" value={backtestedResult.risk_metrics.gross_profit} />
                          <Metric label="Gross loss" value={backtestedResult.risk_metrics.gross_loss} />
                          <Metric label="Max drawdown" value={backtestedResult.risk_metrics.max_drawdown} />
                          </VStack>
                      </Card.Body>
                  </Card.Root>

                  <Card.Root width="full">
                      <Card.Header><Heading size="md">Trade Metrics</Heading></Card.Header>
                      <Card.Body>
                          <VStack align="start" gap={2}>
                          <Metric label="Total trades" value={backtestedResult.trade_metrics.total_trades} />
                          <Metric label="Total winning trades" value={backtestedResult.trade_metrics.total_winning_trades} />
                          <Metric label="Total losing trades" value={backtestedResult.trade_metrics.total_losing_trades} />
                          <Metric label="Starting balance" value={backtestedResult.trade_metrics.starting_balance} />
                          <Metric label="Finishing balance" value={backtestedResult.trade_metrics.finishing_balance} />
                          <Metric label="Longs count" value={backtestedResult.trade_metrics.longs_count} />
                          <Metric label="Longs percentage" value={backtestedResult.trade_metrics.longs_percentage} />
                          <Metric label="Shorts percentage" value={backtestedResult.trade_metrics.shorts_percentage} />
                          <Metric label="Shorts count" value={backtestedResult.trade_metrics.shorts_count} />
                          <Metric label="Fee" value={backtestedResult.trade_metrics.fee} />
                          <Metric label="Total open trades" value={backtestedResult.trade_metrics.total_open_trades} />
                          <Metric label="Open PL" value={backtestedResult.trade_metrics.open_pl} />
                          </VStack>
                      </Card.Body>
                  </Card.Root>
              </HStack>
          </Box>
      </Container>
    </Box>
  );
};

export default BacktestResultComponent;