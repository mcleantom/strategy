import { Card, Container, Heading, HStack, Text } from "@chakra-ui/react";
import { CloseButton } from "@/components/ui/close-button";
import {
  Box,
  Flex,
  Link,
  IconButton,
  useDisclosure,
  VStack,
} from "@chakra-ui/react";
import { createChart } from "lightweight-charts";
import { useEffect, useRef, useState } from "react";
import { StrategyService, BacktestResult } from "@/client";


const EquityChart = () => {
    const chartContainerRef = useRef(null);
    const [backtestedResult, setBacktestedResult] = useState<BacktestResult | null>(null);
    
    useEffect(() => {
        StrategyService.runStrategyBacktestPost({
          requestBody: {
            timeframe: "4h",
          },
        })
          .then((result) => {
            setBacktestedResult(result);
          })
          .catch((error) => {
            console.error('Error fetching backtest result:', error);
          });
      }, []);
    
    useEffect(() => {
        if (chartContainerRef.current === null || backtestedResult === null) { 
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
  

const Navbar = () => {
  const { open, onOpen, onClose } = useDisclosure();

  const Links = ["Create", "Backtest", "Run", "Dashboard"];

  const NavLink = ({ children }) => (
    <Link
      px={2}
      py={1}
      rounded={"md"}
      _hover={{
        textDecoration: "none",
        bg: "gray.200",
      }}
      href={"#"}
    >
      {children}
    </Link>
  );

  return (
    <Box bg="gray.100" px={4}>
        <Container>
        <Flex h={16} alignItems={"center"} justifyContent={"space-between"}>
            <HStack alignItems={"center"}>
            <Box fontWeight="bold">Strategy</Box>
            <HStack as={"nav"} display={{ base: "none", md: "flex" }}>
                {Links.map((link) => (
                <NavLink key={link}>{link}</NavLink>
                ))}
            </HStack>
            </HStack>
            <IconButton
                size={"md"}
                aria-label={"Open Menu"}
                display={{ md: "none" }}
                onClick={onOpen}
            >
                <CloseButton/>
            </IconButton>
        </Flex>

        {open ? (
            <Box pb={4} display={{ md: "none" }}>
            <VStack as={"nav"}>
                {Links.map((link) => (
                <NavLink key={link}>{link}</NavLink>
                ))}
                <CloseButton onClick={onClose} />
            </VStack>
            </Box>
        ) : null}
      </Container>
    </Box>
  );
};


const Metric: React.FC<{ label: string; value: string | number }> = ({ label, value }) => {
    return (
      <HStack justify="space-between" width="100%">
        <Text>{label}:</Text>
        <Text>{value}</Text>
      </HStack>
    );
};

const Demo = () => {
    return (
      <Box>
        <Navbar />
        <Container>
            <Box p={4}>
                <Card.Root>
                    <Card.Header><Heading size="md">Equity Curve</Heading></Card.Header>
                    <Card.Body>
                        <EquityChart/>
                    </Card.Body>
                </Card.Root>
                <HStack flexDirection={{ base: "column", md: "row" }} pt={4} gap="4" justify="center" width="100%" alignItems={"flex-start"}>
                    <Card.Root width="full">
                        <Card.Header><Heading size="md">Performance Metrics</Heading></Card.Header>
                        <Card.Body>
                            <VStack align="start" gap={2}>
                            <Metric label="PNL" value="3919.60 (39.20%)" />
                            <Metric label="Win rate" value="48.57%" />
                            <Metric label="Sharpe ratio" value="1.07" />
                            <Metric label="mdart Sharpe" value="1.06" />
                            <Metric label="Sortino ratio" value="1.86" />
                            <Metric label="mdart Sortino" value="1.84" />
                            <Metric label="Calmar ratio" value="2.01" />
                            <Metric label="Omega ratio" value="1.30" />
                            <Metric label="Serenity index" value="0.35" />
                            <Metric label="Average win/loss" value="0.00" />
                            <Metric label="Average win" value="828.37" />
                            <Metric label="Average loss" value="564.59" />
                            </VStack>
                        </Card.Body>
                    </Card.Root>

                    <Card.Root width="full">
                        <Card.Header><Heading size="md">Risk Metrics</Heading></Card.Header>
                        <Card.Body>
                            <VStack align="start" gap={2}>
                            <Metric label="Total losing streak" value="5" />
                            <Metric label="Largest losing trade" value="-1151.53" />
                            <Metric label="Largest winning trade" value="1892.20" />
                            <Metric label="Total winning streak" value="6" />
                            <Metric label="Current streak" value="1" />
                            <Metric label="Expectancy" value="111.99 (1.12%)" />
                            <Metric label="Expected net profit" value="111.99" />
                            <Metric label="Average holding period" value="343683.43" />
                            <Metric label="Gross profit" value="14082.23" />
                            <Metric label="Gross loss" value="-10162.63" />
                            <Metric label="Max drawdown" value="-19.59" />
                            </VStack>
                        </Card.Body>
                    </Card.Root>

                    <Card.Root width="full">
                        <Card.Header><Heading size="md">Trade Metrics</Heading></Card.Header>
                        <Card.Body>
                            <VStack align="start" gap={2}>
                            <Metric label="Total trades" value="35" />
                            <Metric label="Total winning trades" value="17" />
                            <Metric label="Total losing trades" value="18" />
                            <Metric label="Starting balance" value="10000.00" />
                            <Metric label="Finishing balance" value="13919.60" />
                            <Metric label="Longs count" value="1" />
                            <Metric label="Longs percentage" value="2.86" />
                            <Metric label="Shorts percentage" value="97.14" />
                            <Metric label="Shorts count" value="34" />
                            <Metric label="Fee" value="346.63" />
                            <Metric label="Total open trades" value="1" />
                            <Metric label="Open PL" value="739.11" />
                            </VStack>
                        </Card.Body>
                    </Card.Root>
                </HStack>
            </Box>
        </Container>
      </Box>
    );
  };

export default Demo;