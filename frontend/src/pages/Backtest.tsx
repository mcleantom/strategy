import { BacktestService, ListBacktestIdsResultItem, ETimeframe, StrategiesService } from "@/client";
import { Navbar } from "@/components/navbar";
import { toaster, Toaster } from "@/components/ui/toaster";
import { Box, Button, Card, Container, createListCollection, SelectContent, SelectItem, SelectLabel, SelectRoot, SelectTrigger, SelectValueText, Table } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";


const NewBacktestComponent = () => {
    const timeframes: ETimeframe[] = [
        "1m", "2m", "3m", "15m", "30m", "45m", "1h", "2h", "3h", "4h", "6h", "8h", "12h", "1D", "3D", "1W"
    ];
    const timeframeCollection = createListCollection({
        items: timeframes.map(timeframe => {
            return {
                label: timeframe, value: timeframe
            }
        })
    });
    const [strategiesCollection, setStrategiesCollection] = useState(createListCollection({items: [{ label: "", value: "" }]}));
    const [selectedTimeframe, setSelectedTimeframe] = useState<ETimeframe | null>(null);
    const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);

    useEffect(() => {
        StrategiesService.getStrategiesStrategiesGet()
            .then(strategies => {
                const newStrategiesCollection = createListCollection({
                    items: strategies.map(strategy => ({
                        label: strategy,
                        value: strategy
                    }))
                });
                setStrategiesCollection(newStrategiesCollection);
            })
            .catch(_ => {
                toaster.create({
                    title: "Could not load strategies"
                });
            })
    }, []);

    const handleSubmitBacktest = () => {
        if (selectedTimeframe && selectedStrategy) {
            BacktestService.runBacktestBacktestsPost({
                requestBody: {
                    timeframe: selectedTimeframe,
                    strategy: selectedStrategy
                }
            }).then(_ => {
                toaster.create({
                    title: "Running backtest"
                });
            }).catch(_ => {
                toaster.create({
                    title: "Error running backtest"
                });
            });
        } else {
            toaster.create({
                title: "Please select both a timeframe and a strategy"
            });
        }
    }

    return (
        <Card.Root mt={4} mb={4}>
            <Card.Header>Create Backtest</Card.Header>
            <Card.Body>
                <SelectRoot collection={timeframeCollection} onValueChange={(e) => setSelectedTimeframe(e.value[0])}>
                    <SelectLabel>Hello</SelectLabel>
                    <SelectTrigger>
                        <SelectValueText placeholder="Select timeframe"/>
                    </SelectTrigger>
                    <SelectContent>
                        {timeframeCollection.items.map((timeframe) => (
                            <SelectItem item={timeframe} key={timeframe.value}>
                                {timeframe.label}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </SelectRoot>
                <SelectRoot collection={strategiesCollection} onValueChange={(e) => setSelectedStrategy(e.value[0])}>
                    <SelectLabel>Strategy</SelectLabel>
                    <SelectTrigger>
                        <SelectValueText placeholder="Select strategy" />
                    </SelectTrigger>
                    <SelectContent>
                        {strategiesCollection.items.map((strategy) => (
                            <SelectItem item={strategy} key={strategy.value}>
                                {strategy.label}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </SelectRoot>
                <Button
                    mt={4}
                    colorScheme="blue"
                    onClick={handleSubmitBacktest}
                >
                    Submit Backtest
                </Button>
            </Card.Body>
        </Card.Root>
    )
};


const BacktestsComponent = () => {
    const [backtestIds, setBacktestIds] = useState<ListBacktestIdsResultItem[]>([]);
    const navigate = useNavigate();
    
    useEffect(() => {
        BacktestService.listBacktestIdsBacktestsGet()
            .then(results => {
                setBacktestIds(results);
            })
            .catch(_ => {
                toaster.create({
                    title: "Failed to load results"
                });
            })
    }, []);
    
    const handleRowClick = (id: number) => {
        navigate(`/backtests/${id}`);
    }

    const handleDeleteResult = (id: number) => {
        BacktestService.deleteBacktestResultBacktestsBacktestIdDelete({
            backtestId: id
        }).then(_ => {
            toaster.create({
                title: "Deleted backtest result"
            });
            setBacktestIds((prevBacktests) => prevBacktests.filter((backtest) => backtest.id !== id));
        }).catch(_ => {
            toaster.create({
                title: "Failed to delete backtest result"
            });
        });
    }

    return (
        <Box>
            <Navbar/>
            <Container>
                <NewBacktestComponent/>
                <Card.Root>
                    <Card.Header>Backtest Results</Card.Header>
                    <Card.Body>
                    {backtestIds.length > 0 ? (
                            <Table.Root>
                                <Table.Header>
                                    <Table.Row>
                                        <Table.ColumnHeader>ID</Table.ColumnHeader>
                                        <Table.ColumnHeader>Strategy Name</Table.ColumnHeader>
                                        <Table.ColumnHeader>Date Created</Table.ColumnHeader>
                                        <Table.ColumnHeader>Delete</Table.ColumnHeader>
                                    </Table.Row>
                                </Table.Header>
                                <Table.Body>
                                    {backtestIds.map((backtest) => (
                                        <Table.Row key={backtest.id} onClick={() => handleRowClick(backtest.id)} _hover={{ bg: "gray.100", cursor: "pointer" }}>
                                            <Table.Cell>{backtest.id}</Table.Cell>
                                            <Table.Cell>{backtest.strategy_name}</Table.Cell>
                                            <Table.Cell>{new Date(backtest.date_created).toLocaleString()}</Table.Cell>
                                            <Table.Cell>
                                                <Button
                                                    colorScheme={"red"}
                                                    size="sm"
                                                    onClick={
                                                        (e) => {
                                                            e.stopPropagation();
                                                            handleDeleteResult(backtest.id);
                                                        }
                                                    }
                                                >
                                                    Delete
                                                </Button>
                                            </Table.Cell>
                                        </Table.Row>
                                    ))}
                                </Table.Body>
                            </Table.Root>
                        ) : (
                            <Box>No backtests found.</Box>
                        )}
                    </Card.Body>
                </Card.Root>
            </Container>
            <Toaster/>
        </Box>
    )
}

export default BacktestsComponent;