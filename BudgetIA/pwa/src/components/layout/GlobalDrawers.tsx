import { useDrawer } from "../../context/DrawerContext";
import CategoryDrawer from "../dashboard/CategoryDrawer";
import BudgetDrawerContent from "../budgets/BudgetDrawerContent";

export function GlobalDrawers() {
    const { drawerState, closeDrawer } = useDrawer();

    return (
        <>
            <CategoryDrawer 
                isOpen={drawerState.isOpen && drawerState.type === 'CATEGORY_EXPENSES'} 
                onClose={closeDrawer}
                highlightCategory={drawerState.highlightCategory}
            />
            <BudgetDrawerContent 
                isOpen={drawerState.isOpen && drawerState.type === 'BUDGETS'} 
                onClose={closeDrawer}
                highlightCategory={drawerState.highlightCategory}
                highlightId={drawerState.highlightId}
            />
        </>
    );
}
