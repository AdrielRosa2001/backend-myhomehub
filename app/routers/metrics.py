from fastapi import APIRouter, Depends, Query
from peewee import fn
from datetime import date, datetime
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/metrics", tags=["Metrics"])

MONTH_NAMES = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
]

@router.get("/summary", response_model=schemas.SummaryResponse)
def get_summary(
    start_date: date = Query(..., description="Data inicial obrigatória"),
    end_date: date = Query(..., description="Data final obrigatória"),
    current_user: models.User = Depends(get_current_user), 
    _: None = Depends(get_db)
):
    # Condição base para reaproveitamento
    date_filter = (models.Transaction.date >= start_date) & (models.Transaction.date <= end_date)

    receitas = models.Transaction.select(fn.SUM(models.Transaction.amount)).where(
        (models.Transaction.type == 'receita') & date_filter
    ).scalar() or 0.0
    
    despesas = models.Transaction.select(fn.SUM(models.Transaction.amount)).where(
        (models.Transaction.type == 'despesa') & date_filter
    ).scalar() or 0.0
    
    return {
        "total_receitas": receitas,
        "total_despesas": despesas,
        "saldo": receitas - despesas
    }

@router.get("/chart-data", response_model=schemas.ChartDataResponse)
def get_chart_data(
    start_date: date = Query(..., description="Data inicial obrigatória"),
    end_date: date = Query(..., description="Data final obrigatória"),
    current_user: models.User = Depends(get_current_user), 
    _: None = Depends(get_db)
):
    query = (models.Transaction
             .select(
                 models.Transaction.date, 
                 models.Transaction.type, 
                 fn.SUM(models.Transaction.amount).alias('total')
             )
             .where(
                 (models.Transaction.date >= start_date) & 
                 (models.Transaction.date <= end_date)
             )
             .group_by(models.Transaction.date, models.Transaction.type))
    
    data_dict = {}
    for row in query:
        r_date = row.date
        r_type = row.type
        total = row.total
        
        if r_date not in data_dict:
            data_dict[r_date] = {"date": r_date, "receitas": 0.0, "despesas": 0.0}
        
        if r_type == "receita":
            data_dict[r_date]["receitas"] += total
        else:
            data_dict[r_date]["despesas"] += total
            
    # Ordena cronologicamente para a renderização do gráfico
    chart_data = sorted(list(data_dict.values()), key=lambda x: x["date"])
    
    return {"data": chart_data}

@router.get("/annual-chart", response_model=schemas.AnnualChartResponse)
def get_annual_chart(
    year: int = Query(..., description="Ano para gerar o relatório (ex: 2026)"),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(get_db)
):
    """
    Retorna dados mensais consolidados do ano inteiro para alimentar
    o gráfico "Relatório Anual".
    """
    query = (models.Transaction
             .select(
                 fn.strftime('%m', models.Transaction.date).alias('month_num'),
                 models.Transaction.type,
                 fn.SUM(models.Transaction.amount).alias('total')
             )
             .where(
                 fn.strftime('%Y', models.Transaction.date) == str(year)
             )
             .group_by(
                 fn.strftime('%m', models.Transaction.date),
                 models.Transaction.type
             ))

    # Inicializa os 12 meses com zero
    monthly = {m: {"receitas": 0.0, "despesas": 0.0} for m in range(1, 13)}

    for row in query:
        m = int(row.month_num)
        if row.type == "receita":
            monthly[m]["receitas"] += row.total
        else:
            monthly[m]["despesas"] += row.total

    data = [
        schemas.MonthlyChartPoint(
            month=MONTH_NAMES[m - 1],
            receitas=monthly[m]["receitas"],
            despesas=monthly[m]["despesas"]
        )
        for m in range(1, 13)
    ]

    return schemas.AnnualChartResponse(year=year, data=data)