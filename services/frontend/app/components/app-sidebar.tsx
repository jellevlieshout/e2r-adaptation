import { Home, List, Search, Wand2, FlaskConical, History, PlusCircle } from "lucide-react";
import { Link, useLocation } from "react-router";
import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarHeader,
} from "~/components/ui/sidebar";

const items = [
    {
        title: "Dashboard",
        url: "/",
        icon: Home,
    },
    {
        title: "Adapt",
        url: "/adapt",
        icon: Wand2,
    },
    {
        title: "History",
        url: "/history",
        icon: History,
    },
    {
        title: "Detect",
        url: "/detect",
        icon: Search,
    },
    {
        title: "Experiment Runs",
        url: "/runs",
        icon: List,
    },
    {
        title: "SemEval Tasks",
        url: "/semeval",
        icon: FlaskConical,
    },
    {
        title: "New Manual Example",
        url: "/manual/new",
        icon: PlusCircle,
    },
];

export function AppSidebar() {
    const location = useLocation();

    return (
        <Sidebar>
            <SidebarHeader className="p-4 border-b">
                <h2 className="text-xl font-bold tracking-tight px-2">E2R Adaptation</h2>
            </SidebarHeader>
            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel>Menu</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {items.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton
                                        asChild
                                        isActive={location.pathname === item.url || (item.url !== "/" && location.pathname.startsWith(item.url))}
                                    >
                                        <Link to={item.url}>
                                            <item.icon className="w-4 h-4 mr-2" />
                                            <span>{item.title}</span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
        </Sidebar>
    );
}
