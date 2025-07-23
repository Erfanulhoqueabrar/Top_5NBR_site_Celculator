import streamlit as st
import pandas as pd
import math
import folium
from streamlit_folium import st_folium
from io import BytesIO

# Haversine formula to calculate distance in km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Load uploaded file - CSV or Excel
def load_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xlsx', '.xls')):
        return pd.read_excel(uploaded_file)
    else:
        st.warning("Unsupported file format. Please upload a .csv or .xlsx file.")
        return None

# Streamlit UI
st.title("📍 Nearest Neighbor Finder with Map & Export")

st.markdown("""
Upload two site files (CSV or Excel):
- **All Sites File**: Columns must include `Site`, `Latitude`, `Longitude`
- **Target Sites File**: Same structure
""")

num_neighbors = st.slider("Number of nearest neighbors", 1, 10, 5)

all_sites_file = st.file_uploader("Upload All Sites File (.csv or .xlsx)", type=["csv", "xlsx"])
target_sites_file = st.file_uploader("Upload Target Sites File (.csv or .xlsx)", type=["csv", "xlsx"])

if all_sites_file and target_sites_file:
    all_sites = load_file(all_sites_file)
    target_sites = load_file(target_sites_file)

    if all_sites is not None and target_sites is not None:
        results = []

        for _, target in target_sites.iterrows():
            t_name = target['Site']
            t_lat = target['Latitude']
            t_lon = target['Longitude']

            distances = []
            for _, site in all_sites.iterrows():
                a_name = site['Site']
                if a_name == t_name:
                    continue
                a_lat = site['Latitude']
                a_lon = site['Longitude']
                dist = haversine(t_lat, t_lon, a_lat, a_lon)
                distances.append((a_name, a_lat, a_lon, round(dist, 3)))

            top_neighbors = sorted(distances, key=lambda x: x[3])[:num_neighbors]
            result = {'Target Site': t_name}
            for i, (site_name, _, _, dist_km) in enumerate(top_neighbors, start=1):
                result[f'Neighbor {i}'] = site_name
                result[f'Distance {i} (km)'] = dist_km
            results.append(result)

        output_df = pd.DataFrame(results)

        if len(target_sites) == 1:
            st.success("✅ Nearest neighbors for single site shown on map:")

            target = target_sites.iloc[0]
            map_center = [target['Latitude'], target['Longitude']]
            m = folium.Map(location=map_center, zoom_start=13)

            # Add target marker (green)
            folium.Marker(
                location=map_center,
                tooltip=f"🎯 Target: {target['Site']}",
                icon=folium.Icon(color='green', icon='star')
            ).add_to(m)

            # Calculate total route distance (target -> neighbors -> target)
            total_distance = 0
            prev_lat, prev_lon = target['Latitude'], target['Longitude']
            for _, lat, lon, dist in top_neighbors:
                total_distance += haversine(prev_lat, prev_lon, lat, lon)
                prev_lat, prev_lon = lat, lon
            total_distance += haversine(prev_lat, prev_lon, target['Latitude'], target['Longitude'])

            st.markdown(f"### 🛣️ Total route distance: **{total_distance:.2f} km**")

            # Add neighbor markers with popup (blue)
            for i, (name, lat, lon, dist) in enumerate(top_neighbors, start=1):
                folium.Marker(
                    location=[lat, lon],
                    popup=f"Neighbor {i}: {name} — {dist} km",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)

            # Display map
            st_folium(m, width=700, height=500)

            # Download map as HTML
            map_html = m._repr_html_()
            map_bytes = map_html.encode('utf-8')

            st.download_button(
                label="📥 Download Map as HTML",
                data=map_bytes,
                file_name=f"{target['Site']}_neighbors_map.html",
                mime="text/html"
            )

            # Google Maps link
            base_url = "https://www.google.com/maps/dir/?api=1"
            origin = f"{target['Latitude']},{target['Longitude']}"
            waypoints = "|".join([f"{lat},{lon}" for _, lat, lon, _ in top_neighbors])
            map_url = f"{base_url}&origin={origin}&destination={origin}&travelmode=driving&waypoints={waypoints}"

            st.markdown("### 🗺️ Open in Google Maps:")
            st.markdown(f"[Click here to view route in Google Maps]({map_url})", unsafe_allow_html=True)

        else:
            st.success("✅ Nearest neighbors calculated for multiple target sites:")
            st.dataframe(output_df)

            # CSV Export
            csv = output_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "nearest_neighbors.csv", "text/csv")

            # Excel Export
            excel_io = BytesIO()
            with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
                output_df.to_excel(writer, index=False, sheet_name='Neighbors')
            st.download_button("📥 Download Excel", excel_io.getvalue(), "nearest_neighbors.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
