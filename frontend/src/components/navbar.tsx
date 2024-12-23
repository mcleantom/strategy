import { useDisclosure, Link, Box, Container, Flex, HStack, IconButton, VStack } from "@chakra-ui/react";
import { CloseButton } from "./ui/close-button";


export const Navbar = () => {
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
            <CloseButton />
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
