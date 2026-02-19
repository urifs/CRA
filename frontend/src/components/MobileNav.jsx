import { NavLink } from "react-router-dom";
import { 
  LayoutDashboard, 
  Truck, 
  Wrench, 
  HardHat,
  MoreHorizontal
} from "lucide-react";

export default function MobileNav() {
  const navItems = [
    { path: "/dashboard", icon: LayoutDashboard, label: "Início" },
    { path: "/obras", icon: HardHat, label: "Obras" },
    { path: "/machines", icon: Truck, label: "Máquinas" },
    { path: "/maintenances", icon: Wrench, label: "Manutenções" },
    { path: "/more", icon: MoreHorizontal, label: "Mais" },
  ];

  return (
    <nav className="mobile-nav" data-testid="mobile-nav">
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
            `mobile-nav-item no-select ${isActive ? "active" : ""}`
          }
          data-testid={`mobile-nav-${item.path.replace("/", "")}`}
        >
          <item.icon />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
