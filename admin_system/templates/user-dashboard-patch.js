// Changes to make:
// 1. Remove filteredEl reference in renderBudgets
// 2. Add onchange handler to amount input
// 3. Add updateBudgetAmountRealtime function
// 4. Remove loadEducationBudgets call

// Line 910-915: Remove filtered total logic
function renderBudgets(list, totalOverall) {
    const tableBody = document.getElementById('budgetList');
    const totalEl = document.getElementById('budgetTotal');
    
    totalEl.textContent = `₱${(totalOverall || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`;

// Line ~930: Add onchange to amount input  
<input type="number" value="${budget.amount}" data-id="${budget.id}" data-field="amount" step="0.01" style="width: 120px; padding: 6px;" onchange="updateBudgetAmountRealtime(${budget.id}, this.value)">

// After loadBudgets function: Add real-time update function
function updateBudgetAmountRealtime(budgetId, newAmount) {
    const budget = budgetsCache.find(b => b.id === budgetId);
    if (budget) {
        budget.amount = parseFloat(newAmount) || 0;
        const total = budgetsCache.reduce((sum, b) => sum + (parseFloat(b.amount) || 0), 0);
        document.getElementById('budgetTotal').textContent = `₱${total.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    }
}

// Remove loadEducationBudgets() from upload handler and init
