
import streamlit as st
import pandas as pd
import math
from io import StringIO

# Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Streamlit UI
st.title("🔍 Nearest Neighbor Finder (Haversine)")

st.markdown("""
Upload two CSV files:
- **All Sites File**: Must include columns `Site`, `Latitude`, `Longitude`
- **Target Sites File**: Must include the same structure
""")

all_sites_file = st.file_uploader("Upload All Sites CSV", type="csv")
target_sites_file = st.file_uploader("Upload Target Sites CSV", type="csv")

if all_sites_file and target_sites_file:
    all_sites = pd.read_csv(all_sites_file)
    target_sites = pd.read_csv(target_sites_file)

    results = []

    for _, target in target_sites.iterrows():
        t_name = target['Site']
        t_lat = target['Latitude']
        t_lon = target['Longitude']

        distances = []
        for _, site in all_sites.iterrows():
            a_name = site['Site']
            a_lat = site['Latitude']
            a_lon = site['Longitude']
            dist = haversine(t_lat, t_lon, a_lat, a_lon)
            distances.append((a_name, round(dist, 3)))

        top5 = sorted(distances, key=lambda x: x[1])[:5]
        result = {'Target Site': t_name}
        for i, (site_name, dist_km) in enumerate(top5, start=1):
            result[f'Neighbor {i}'] = site_name
            result[f'Distance {i} (km)'] = dist_km
        results.append(result)

    output_df = pd.DataFrame(results)
    st.success("✅ Nearest neighbors calculated!")

    st.dataframe(output_df)

    # Download button
    csv = output_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Result CSV",
        data=csv,
        file_name='nearest_neighbors_result.csv',
        mime='text/csv',
    )
