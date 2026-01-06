import { Home, CreditCard, Bot, Link as LinkIcon, User, Tag } from "lucide-react";

export const navigationItems = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Transações', href: '/transactions', icon: CreditCard },
  { name: 'Inteligência', href: '/intelligence', icon: Bot },
  { name: 'Conexões', href: '/connections', icon: LinkIcon },
  { name: 'Perfil', href: '/profile', icon: User },
];
