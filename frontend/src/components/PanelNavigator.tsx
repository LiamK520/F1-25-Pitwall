export type DashboardTab = "live" | "analysis" | "session"

interface PanelNavigatorProps {
    activeTab: DashboardTab
    onTabChange: (tab: DashboardTab) => void
}

function PanelNavigator({activeTab, onTabChange}: PanelNavigatorProps) {
    return (
        <nav className="panel-navigator">
            <button
                onClick={() => onTabChange("live")}
                disabled={activeTab === "live"}
            >
                Live
            </button>

            <button
                onClick={() => onTabChange("analysis")}
                disabled={activeTab === "analysis"}
            >
                Analysis
            </button>

            <button
                onClick={() => onTabChange("session")}
                disabled={activeTab === "session"}
            >
                Session
            </button>
        </nav>
    )
}


export default PanelNavigator