import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def create_bar_chart(df, label_col, value_col, title, color='#1f77b4'):
    """Cria gráfico de barras horizontal."""
    if df is None or df.empty:
        return None

    # Ordenar por valor
    df_sorted = df.sort_values(by=value_col, ascending=True)

    fig = px.bar(
        df_sorted,
        y=label_col,
        x=value_col,
        title=title,
        orientation='h',
        text=value_col,
        color_discrete_sequence=[color]
    )

    fig.update_traces(
        textposition='outside',
        texttemplate='%{text:,}',
        marker_line_width=0
    )

    fig.update_layout(
        title={'x': 0.5, 'xanchor': 'center', 'font': {'size': 14}},
        xaxis_title='Número de Eventos',
        yaxis_title='',
        height=max(350, len(df_sorted) * 35),
        margin=dict(l=10, r=30, t=50, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial', 'size': 10}
    )

    return fig


def create_pie_chart(df, label_col, value_col, title, color_sequence=None):
    """Cria gráfico de pizza."""
    if df is None or df.empty:
        return None

    fig = px.pie(
        df,
        names=label_col,
        values=value_col,
        title=title,
        hole=0.4,
        color_discrete_sequence=color_sequence
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=9
    )

    fig.update_layout(
        title={'x': 0.5, 'xanchor': 'center', 'font': {'size': 14}},
        height=450,
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=True,
        legend={'font': {'size': 9}, 'orientation': 'h', 'y': -0.1}
    )

    return fig


def create_distribution_chart(df, label_col, value_col, title):
    """Cria gráfico de distribuição (pizza + barra combinados)."""
    if df is None or df.empty:
        return None

    # Calcular percentuais
    total = df[value_col].sum()
    df_copy = df.copy()
    df_copy['percent'] = (df_copy[value_col] / total * 100).round(1)

    # Criar gráfico de pizza
    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=df_copy[label_col],
        values=df_copy[value_col],
        hole=0.5,
        textinfo='percent',
        textfont_size=10,
        marker_colors=px.colors.qualitative.Set3
    ))

    fig.update_layout(
        title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 14}},
        height=450,
        showlegend=True,
        legend={'font': {'size': 8}, 'orientation': 'h', 'y': -0.1}
    )

    return fig
