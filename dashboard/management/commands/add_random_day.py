from django.core.management.base import BaseCommand
import pandas as pd
import os
from datetime import datetime
from dashboard.utils import append_to_financial_csv, generate_realistic_next_prices

class Command(BaseCommand):
    help = 'Appends one new row with realistic commodity prices to the CSV (for testing)'

    def handle(self, *args, **options):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                               '..', 'data', 'financial_data.csv')

        if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
            self.stdout.write(self.style.ERROR("CSV file not found or empty"))
            return

        df = pd.read_csv(csv_path)
        if df.empty:
            self.stdout.write(self.style.ERROR("No data in CSV"))
            return

        # Use current timestamp so every run is unique
        next_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        last_row = df.iloc[-1]
        prev_gold   = float(last_row['gold_price'])
        prev_silver = float(last_row['silver_price'])
        prev_oil    = float(last_row['oil_price'])

        new_gold, new_silver, new_oil = generate_realistic_next_prices(
            prev_gold, prev_silver, prev_oil
        )

        new_row = {
            'date': next_date,
            'gold_price': new_gold,
            'silver_price': new_silver,
            'oil_price': new_oil
        }

        success, msg = append_to_financial_csv(new_row)  # utils.py returns 2 values now

        if success:
            self.stdout.write(self.style.SUCCESS(
                f"{msg} → Gold: {new_gold} | Silver: {new_silver} | Oil: {new_oil}"
            ))
        else:
            self.stdout.write(self.style.WARNING(msg))
