#plotly interactive plots
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
from dash import dash_table
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# -------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------
df = pd.read_csv("wine.csv")
df.columns = df.columns.str.strip()

# -------------------------------------------------------------
# CREATE DASH APP
# -------------------------------------------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# -------------------------------------------------------------
# LAYOUT
# -------------------------------------------------------------
app.layout = html.Div([
    html.H1("🍷 Wine Quality Intelligence Dashboard", style={"textAlign": "center", "color": "#722F37"}),
    html.P("A small interactive website analyzing physico-chemical properties and their impact on wine quality.", style={"textAlign": "center", "fontStyle": "italic"}),

    dcc.Tabs(id="mainTabs", value="overviewTab", children=[
        dcc.Tab(label="Overview", value="overviewTab"),
        dcc.Tab(label="Chemical Analysis", value="graphicsTab"),
        dcc.Tab(label="Data Table", value="tableTab"),
        dcc.Tab(label="Summary Statistics", value="summaryTab"),
    ]),

    html.Hr(),

    # ------------------- FILTERS -------------------
    html.Div([
        html.Div([
            html.Label("Select Quality Score:"),
            dcc.Dropdown(
                id="qualityFilter",
                options=[{"label": "All", "value": "All"}] +
                        [{"label": str(q), "value": q} for q in sorted(df["quality"].unique())],
                value=["All"],
                multi=True,
                style={"width": "95%"}
            )
        ], style={'width': '35%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Alcohol Range (%):"),
            dcc.RangeSlider(
                id="alcoholFilter",
                min=float(df["alcohol"].min()),
                max=float(df["alcohol"].max()),
                value=[float(df["alcohol"].min()), float(df["alcohol"].max())],
                marks={i: str(i) for i in range(int(df["alcohol"].min()), int(df["alcohol"].max())+1)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'width': '60%', 'display': 'inline-block', 'paddingLeft': '5%'})
    ], style={"padding": "15px", "backgroundColor": "#f9f9f9", "borderRadius": "5px"}),

    html.Hr(),

    html.Div(id="tabContent"),
    dcc.Store(id="filteredData")
])

# -------------------------------------------------------------
# CALLBACK → FILTER DATA
# -------------------------------------------------------------
@app.callback(
    Output("filteredData", "data"),
    [Input("qualityFilter", "value"),
     Input("alcoholFilter", "value")]
)
def filter_data(qualitysel, alcoholrange):
    low, high = alcoholrange
    dff = df.copy()

    if "All" not in qualitysel:
        dff = dff[dff["quality"].isin(qualitysel)]

    dff = dff[(dff["alcohol"] >= low) & (dff["alcohol"] <= high)]
    return dff.to_dict("records")

# -------------------------------------------------------------
# CALLBACK → MAIN TABS
# -------------------------------------------------------------
@app.callback(
    Output("tabContent", "children"),
    [Input("mainTabs", "value"),
     Input("filteredData", "data")]
)
def render_tabs(tab, data):
    if not data:
        return html.Div("Loading data...")

    dff = pd.DataFrame(data)

    if tab == "overviewTab":
        fig = go.Figure(go.Histogram(x=dff["quality"], marker_color="#722F37"))
        fig.update_layout(title="Distribution of Wine Quality Scores", xaxis_title="Quality", yaxis_title="Count")

        return html.Div([
            html.H3("Overview of Wine Quality Dataset"),
            html.P("This dashboard provides insights into how chemical features affect wine ratings."),
            dcc.Graph(figure=fig),
            html.Div([
                html.Div([
                    html.H4("Key Insight 1"),
                    html.P("Higher alcohol content often correlates with better quality scores in sampled wines.")
                ], style={"width": "48%", "display": "inline-block", "padding": "10px", "border": "1px solid #ddd"}),
                html.Div([
                    html.H4("Key Insight 2"),
                    html.P("Volatile acidity negatively impacts the sensory score, acting as a primary defect indicator.")
                ], style={"width": "48%", "display": "inline-block", "padding": "10px", "border": "1px solid #ddd", "float": "right"})
            ])
        ])

    if tab == "graphicsTab":
        return html.Div([
            dcc.Tabs(id="nestedTabs", value="scatter", children=[
                dcc.Tab(label="Alcohol vs Volatile Acidity", value="scatter"),
                dcc.Tab(label="pH & Sulphates", value="box"),
                dcc.Tab(label="Residual Sugar Trend", value="bar")
            ]),
            html.Div(id="nestedContent", style={"paddingTop": "20px"})
        ])

    if tab == "tableTab":
        return html.Div([
            html.H3("Filtered Data Table (6 Columns)"),
            dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in dff.columns],
                data=dff.to_dict("records"),
                page_size=12,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "center"},
                filter_action="native",
                sort_action="native"
            )
        ])

    if tab == "summaryTab":
        return html.Div([
            html.H3("Summary Statistics"),
            html.Pre(dff.describe().to_string(), style={"background": "#f4f4f4", "padding": "15px", "borderRadius": "5px"})
        ])

# -------------------------------------------------------------
# CALLBACK → NESTED GRAPH TABS
# -------------------------------------------------------------
@app.callback(
    Output("nestedContent", "children"),
    [Input("nestedTabs", "value"),
     Input("filteredData", "data")]
)
def nested_graphs(nestedTab, data):
    if not data:
        return html.Div("Waiting for data...")

    dff = pd.DataFrame(data)

    if nestedTab == "scatter":
        fig = go.Figure(data=go.Scatter(
            x=dff["alcohol"],
            y=dff["volatile_acidity"],
            mode="markers",
            marker=dict(size=10, color=dff["quality"], colorscale="Viridis", showscale=True, title="Quality")
        ))
        fig.update_layout(title="Alcohol vs Volatile Acidity (Colored by Quality)", xaxis_title="Alcohol", yaxis_title="Volatile Acidity")
        return dcc.Graph(figure=fig)

    if nestedTab == "box":
        fig = go.Figure(data=go.Box(y=dff["sulphates"], name="Sulphates", marker_color="#85144b"))
        fig.update_layout(title="Distribution of Sulphates")
        return dcc.Graph(figure=fig)

    if nestedTab == "bar":
        if len(dff) > 0:
            avg_sugar = dff.groupby("quality")["residual_sugar"].mean().reset_index()
            fig = go.Figure(go.Bar(x=avg_sugar["quality"], y=avg_sugar["residual_sugar"], marker_color="#2ECC40"))
            fig.update_layout(title="Average Residual Sugar by Quality Score", xaxis_title="Quality", yaxis_title="Mean Residual Sugar")
        else:
            fig = go.Figure()
        return dcc.Graph(figure=fig)

# -------------------------------------------------------------
# RUN APP
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
