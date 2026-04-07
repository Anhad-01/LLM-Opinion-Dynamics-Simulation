from anvil import *
import anvil.server
import plotly.graph_objects as go

class ModernOpinionDashboard(ColumnPanel):
    def __init__(self, **properties):
        super().__init__(**properties)
        self.role = "elevated-card"
        
        # Build UI creatively using Python classes
        self.title = Label(text="🌐 Global Debate Simulator", font_size=32, bold=True, align="center")
        self.title.foreground = "#2c3e50"
        self.add_component(self.title)
        
        self.subtitle = Label(text="Powered by Gemini Multi-Agent Swarms & Anvil", font_size=16, align="center", italic=True)
        self.add_component(self.subtitle)
        
        self.add_component(Spacer(height=20))
        
        self.config_panel = GridPanel()
        self.agent_input = TextBox(type="number", text="3", placeholder="Agents (e.g. 5)")
        self.round_input = TextBox(type="number", text="3", placeholder="Rounds (e.g. 3)")
        self.topic_input = TextArea(text="Should a global, mandatory carbon tax be implemented?", placeholder="Enter Debate Topic...")
        
        # Add labels and inputs in a Grid Panel
        self.config_panel.add_component(Label(text="Number of Agents:", bold=True), row="A", col_xs=0, width_xs=2)
        self.config_panel.add_component(self.agent_input, row="A", col_xs=2, width_xs=4)
        
        self.config_panel.add_component(Label(text="Number of Rounds:", bold=True), row="A", col_xs=6, width_xs=2)
        self.config_panel.add_component(self.round_input, row="A", col_xs=8, width_xs=4)
        
        self.config_panel.add_component(Label(text="Debate Topic:", bold=True), row="B", col_xs=0, width_xs=2)
        self.config_panel.add_component(self.topic_input, row="B", col_xs=2, width_xs=10)
        
        self.add_component(self.config_panel)
        self.add_component(Spacer(height=20))
        
        self.start_btn = Button(text="🚀 Launch Neural Simulation", role="primary-color", align="center", font_size=18)
        self.start_btn.set_event_handler('click', self.run_simulation)
        self.add_component(self.start_btn)
        
        self.log_panel = RichText(align="left")
        self.add_component(self.log_panel)
        
        self.plot_panel = Plot()
        self.add_component(self.plot_panel)
        
    def run_simulation(self, **event_args):
        self.start_btn.enabled = False
        self.start_btn.text = "⏳ Generating emergent dynamics (please wait)..."
        self.log_panel.content = "### Initializing multi-agent debate servers..."
        
        try:
            # We call the uplink server backend
            # Note: User will need to connect their backend running on local PC using anvil.server.connect("UPLINK_KEY")
            results = anvil.server.call(
                'run_opinion_dynamics', 
                int(self.agent_input.text), 
                int(self.round_input.text), 
                self.topic_input.text
            )
            
            # Format UI visually
            self.log_panel.content = f"### ✅ Debate Completed! Extracted {len(results)} distinct evaluations."
            
            # Use Plotly on the frontend via Anvil's integration
            fig = go.Figure()
            
            # Assuming results is a list of dicts: [{'Round':1, 'Agent_ID':'Agent_1', 'Stance_Score': 7, 'Statement_Summary': '...'}, ...]
            agents = list(set([r['Agent_ID'] for r in results]))
            
            for ag in agents:
                ag_data = [r for r in results if r['Agent_ID'] == ag]
                ag_data = sorted(ag_data, key=lambda x: x['Round'])
                
                fig.add_trace(go.Scatter(
                    x=[r['Round'] for r in ag_data], 
                    y=[r['Stance_Score'] for r in ag_data], 
                    mode='lines+markers', 
                    name=ag,
                    hovertemplate="Stance: %{y}<br>Summary: %{text}",
                    text=[r.get('Statement_Summary', '') for r in ag_data],
                    marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')),
                    line=dict(width=3)
                ))
            
            fig.update_layout(
                title="Agent Opinion Drift Over Time", 
                xaxis_title="Simulation Rounds", 
                yaxis_title="Stance Sentiment Score (1-10)",
                plot_bgcolor='rgba(240, 240, 240, 0.9)',
                hovermode='closest'
            )
            
            self.plot_panel.figure = fig
            
        except Exception as e:
            self.log_panel.content = f"### ❌ Error occurred (make sure Uplink server is running): {str(e)}"
            
        finally:
            self.start_btn.enabled = True
            self.start_btn.text = "🚀 Launch Neural Simulation"
