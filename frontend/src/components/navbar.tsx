import { useDisclosure, Link, Box, Container, Flex, HStack, IconButton, VStack } from "@chakra-ui/react";
import { CloseButton } from "./ui/close-button";

interface NavLink {
  name: string,
  link: string
};

export const Navbar = () => {
  const { open, onOpen, onClose } = useDisclosure();

  const Links: NavLink[] = [
    {
      name: "Strategies",
      link: "/strategies"
    },
    {
      name: "Backtest",
      link: "/backtest"
    }
  ];

  const NavLinkComponent = ({ link }: { link: NavLink }) => (
    <Link
      px={2}
      py={1}
      rounded={"md"}
      _hover={{
        textDecoration: "none",
        bg: "gray.200",
      }}
      href={link.link}
    >
      {link.name}
    </Link>
  );

  const toggleButton = () => {
    if (open) {
      onOpen();
    }
    onClose();
  };

  return (
    <Box bg="gray.100" px={4}>
      <Container>
        <Flex h={16} alignItems={"center"} justifyContent={"space-between"}>
          <HStack alignItems={"center"}>
            <Box fontWeight="bold">Strategy</Box>
            <HStack as={"nav"} display={{ base: "none", md: "flex" }}>
              {Links.map((link) => (
                <NavLinkComponent key={link.link} link={link}/>
              ))}
            </HStack>
          </HStack>
          <IconButton
            size={"md"}
            aria-label={"Open Menu"}
            display={{ md: "none" }}
            onClick={toggleButton}
          >
            <CloseButton />
          </IconButton>
        </Flex>

        {open ? (
          <Box pb={4} display={{ md: "none" }}>
            <VStack as={"nav"}>
              {Links.map((link) => (
                <NavLinkComponent key={link.link} link={link}/>
              ))}
              <CloseButton onClick={toggleButton} />
            </VStack>
          </Box>
        ) : null}
      </Container>
    </Box>
  );
};
