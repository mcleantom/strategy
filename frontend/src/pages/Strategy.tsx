import { StrategiesService } from "@/client";
import { Navbar } from "@/components/navbar";
import { Box, Button, Card, Container, Heading, Input, Text, VStack } from "@chakra-ui/react"
import { useEffect, useState } from "react";
import { Toaster, toaster } from "@/components/ui/toaster"
import { Editor } from "@monaco-editor/react";
import { InputGroup } from "@/components/ui/input-group";


const Strategy = () => {
    const [strategies, setStrategies] = useState<string[]>([]);
    const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
    const [editorContent, setEditorContent] = useState<string>("");
    const [newStrategyName, setNewStrategyName] = useState<string>("");

    useEffect(() => {
        StrategiesService.getStrategiesStrategiesGet()
            .then(strategies => setStrategies(strategies))
            .catch(err => toaster.create({title: "Error", description: JSON.stringify(err)}))
    }, []);

    const handleCreateStrategy = async () => {
        StrategiesService.createStrategyStrategyPost({
            requestBody: {
                name: newStrategyName
            }
        }).then(_ => toaster.create({title: "Created strategy"}))
        .catch(err => toaster.create({title: "Error", description: JSON.stringify(err)}));
    };

    const handleSelectStrategy = async (name: string) => {
        StrategiesService.getStrategyStrategyNameGet({
            name
        }).then(result => {
            setSelectedStrategy(name);
            setEditorContent(result);
            toaster.create({title: "Loaded strategy"})
        }).catch(err => {
            toaster.create({title: "Error", description: JSON.stringify(err)})
        });
    };

    const handleSaveStrategy = async () => {
        if (!selectedStrategy) return;

        const blob = new Blob([editorContent], { type: "text/plain" });
        const formData = new FormData();
        formData.append("file", blob, `${selectedStrategy}.py`);
        StrategiesService.updateStrategyStrategyNamePut({
            name: selectedStrategy,
            formData: {
                file: blob
            }
        }).then(_ => {
            toaster.create({
                title: "Saved"
            })
        }).catch(err => {
            toaster.create({
                title: "Error saving",
                description: JSON.stringify(err)
            })
        })
    }
    

    return (
        <Box>
            <Navbar/>
            <Container>
            <Box p={4}>
                    <Card.Root>
                        <Card.Header>
                        <Heading size="md">
                            <InputGroup width="100%" endElement={<Button onClick={handleCreateStrategy}>Create</Button>}>
                                <Input placeholder="Strategy Name" value={newStrategyName} onChange={(e) => setNewStrategyName(e.target.value)}/>
                            </InputGroup>
                        </Heading>
                        </Card.Header>
                        <Card.Body>
                        <VStack align="stretch" mt={4}>
                            <Box>
                                <Text>Existing Strategies:</Text>
                                {strategies.map((strategy) => (
                                    <Button
                                        key={strategy}
                                        onClick={() => handleSelectStrategy(strategy)}
                                        variant="outline"
                                        colorScheme="teal"
                                        mt={1}
                                    >
                                        {strategy}
                                    </Button>
                                ))}
                            </Box>
                        </VStack>
                        </Card.Body>
                    </Card.Root>
                    {selectedStrategy && (
                        <Card.Root>
                            <Card.Header>{selectedStrategy}</Card.Header>
                            <Card.Body>
                                <Editor
                                    height="90vh"
                                    defaultLanguage="python"
                                    value={editorContent}
                                    onChange={(value) => setEditorContent(value || "")}
                                />
                                <Button onClick={handleSaveStrategy}>Save</Button>
                            </Card.Body>
                        </Card.Root>
                    )}
                    
                </Box>
            </Container>
            <Toaster/>
        </Box>
    )
};

export default Strategy;