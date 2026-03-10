import { FlaskConical } from "lucide-react";
import { Link, useLocation } from "react-router";
import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarHeader,
} from "~/components/ui/sidebar";

const items = [
    {
        title: "Runs",
        url: "/",
        icon: FlaskConical,
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
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {items.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton
                                        asChild
                                        isActive={location.pathname === item.url || location.pathname.startsWith("/runs")}
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
