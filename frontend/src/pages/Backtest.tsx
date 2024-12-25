import { BacktestService, ListBacktestIdsResultItem } from "@/client";
import { Navbar } from "@/components/navbar";
import { toaster, Toaster } from "@/components/ui/toaster";
import { Box, Button, Card, Container, Table } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const BacktestsComponent = () => {
    const [backtestIds, setBacktestIds] = useState<ListBacktestIdsResultItem[]>([]);
    const navigate = useNavigate();
    
    useEffect(() => {
        BacktestService.listBacktestIdsBacktestsGet()
            .then(results => {
                setBacktestIds(results);
            })
            .catch(err => {
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
        }).then(result => {
            toaster.create({
                title: "Deleted backtest result"
            });
            setBacktestIds((prevBacktests) => prevBacktests.filter((backtest) => backtest.id !== id));
        }).catch(err => {
            toaster.create({
                title: "Failed to delete backtest result"
            });
        });
    }

    return (
        <Box>
            <Navbar/>
            <Container>
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