import { Header } from "./Header";

export function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      <main>{children}</main>
    </div>
  );
}
