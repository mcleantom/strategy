import {
  useDisclosure,
  Box,
  Container,
  Flex,
  HStack,
  IconButton,
  VStack,
  Button,
} from "@chakra-ui/react";
import { useNavigate } from "react-router-dom";
import { CloseButton } from "./ui/close-button";

interface NavLink {
  name: string;
  link: string;
}

export const Navbar = () => {
  const { open, onOpen, onClose } = useDisclosure();
  const navigate = useNavigate();

  const Links: NavLink[] = [
    {
      name: "Strategies",
      link: "/strategies",
    },
    {
      name: "Backtest",
      link: "/backtests",
    },
  ];

  const NavLinkComponent = ({ link }: { link: NavLink }) => (
    <Button
      px={2}
      py={1}
      variant="ghost"
      rounded="md"
      _hover={{
        textDecoration: "none",
        bg: "gray.200",
      }}
      onClick={() => navigate(link.link)}
    >
      {link.name}
    </Button>
  );

  const toggleButton = () => {
    if (open) {
      onClose();
    } else {
      onOpen();
    }
  };

  return (
    <Box bg="gray.100" px={4}>
      <Container>
        <Flex h={16} alignItems="center" justifyContent="space-between">
          <HStack alignItems="center">
            <Box fontWeight="bold">Strategy</Box>
            <HStack as="nav" display={{ base: "none", sm: "flex" }}>
              {Links.map((link) => (
                <NavLinkComponent key={link.link} link={link} />
              ))}
            </HStack>
          </HStack>
          <IconButton
            size="md"
            aria-label="Open Menu"
            display={{ sm: "none" }}
            onClick={toggleButton}
          >
            <CloseButton />
          </IconButton>
        </Flex>

        {open && (
          <Box pb={4} display={{ sm: "none" }}>
            <VStack as="nav">
              {Links.map((link) => (
                <NavLinkComponent key={link.link} link={link} />
              ))}
              <CloseButton onClick={toggleButton} />
            </VStack>
          </Box>
        )}
      </Container>
    </Box>
  );
};
