# dashboard/app.py - UPDATED WITH NULL HANDLING
import streamlit as st
import requests
import plotly.graph_objects as go
import json

st.set_page_config(page_title="France Energy AI", layout="wide")
st.title("🇫🇷 France Energy AI Dashboard")
st.markdown("Real-time analysis of France's energy grid")

# Sidebar
st.sidebar.header("Settings")
api_url = st.sidebar.text_input("API URL", "http://localhost:8001")

# Helper function to format numbers safely
def format_number(value):
    """Safely format a number, handling None/NaN"""
    if value is None:
        return "0"
    try:
        return f"{float(value):,}"
    except (ValueError, TypeError):
        return "0"

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Ask about France's energy:",
        "What is the current energy mix in France?"
    )
    
    if st.button("Analyze", type="primary"):
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(
                    f"{api_url}/analyze",
                    json={"query": query},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        st.success("✅ Analysis Complete")
                        
                        # Show analysis
                        st.subheader("Analysis")
                        st.write(result.get("analysis", "No analysis available"))
                        
                        # Show data with safe formatting
                        with st.expander("📊 View Data"):
                            if "data" in result:
                                data = result["data"]
                                
                                # Create metrics with safe formatting
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("⚡ Production", f"{format_number(data.get('production_MW'))} MW")
                                    st.metric("🔌 Consumption", f"{format_number(data.get('consumption_MW'))} MW")
                                    st.metric("☢️ Nuclear", f"{format_number(data.get('nuclear_MW'))} MW")
                                
                                with col2:
                                    st.metric("🌬️ Wind", f"{format_number(data.get('wind_MW'))} MW")
                                    st.metric("🌞 Solar", f"{format_number(data.get('solar_MW'))} MW")
                                    st.metric("🌊 Hydro", f"{format_number(data.get('hydro_MW'))} MW")
                                
                                with col3:
                                    st.metric("🏭 Gas", f"{format_number(data.get('gas_MW'))} MW")
                                    st.metric("🌍 CO2", f"{format_number(data.get('carbon_intensity'))} g/kWh")
                                    st.metric("🕐 Updated", data.get('timestamp', 'N/A'))
                                
                                # Create pie chart only if we have positive values
                                production = float(format_number(data.get('production_MW')).replace(',', ''))
                                if production > 0:
                                    st.subheader("Energy Mix")
                                    
                                    # Get values safely
                                    mix_data = {}
                                    sources = [
                                        ("Nuclear", data.get('nuclear_MW')),
                                        ("Wind", data.get('wind_MW')),
                                        ("Solar", data.get('solar_MW')),
                                        ("Hydro", data.get('hydro_MW')),
                                        ("Gas", data.get('gas_MW'))
                                    ]
                                    
                                    for name, value in sources:
                                        try:
                                            val = float(value) if value is not None else 0
                                            if val > 0:
                                                mix_data[name] = val
                                        except (ValueError, TypeError):
                                            continue
                                    
                                    if mix_data:
                                        fig = go.Figure(data=[go.Pie(
                                            labels=list(mix_data.keys()),
                                            values=list(mix_data.values()),
                                            hole=0.3,
                                            textinfo='label+percent'
                                        )])
                                        st.plotly_chart(fig)
                                    else:
                                        st.info("No positive production data available for pie chart.")
                    else:
                        st.error(f"Error: {result.get('message', 'Unknown error')}")
                else:
                    st.error(f"API Error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error("Request timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Make sure the server is running.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    st.subheader("Quick Actions")
    
    if st.button("🔄 Get Latest Data"):
        try:
            response = requests.get(
                "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records",
                params={"limit": 1, "order_by": "date desc"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results'):
                    latest = data['results'][0]
                    
                    # Safely extract values
                    def get_safe(key, default=0):
                        val = latest.get(key)
                        return val if val is not None else default
                    
                    # Display metrics with safe formatting
                    st.metric("⚡ Production", f"{format_number(get_safe('production'))} MW")
                    st.metric("🔌 Consumption", f"{format_number(get_safe('consommation'))} MW")
                    st.metric("☢️ Nuclear", f"{format_number(get_safe('nucleaire'))} MW")
                    st.metric("🌬️ Wind", f"{format_number(get_safe('eolien'))} MW")
                    st.metric("🌞 Solar", f"{format_number(get_safe('solaire'))} MW")
                    st.metric("🌊 Hydro", f"{format_number(get_safe('hydraulique'))} MW")
                    st.metric("🏭 Gas", f"{format_number(get_safe('gaz'))} MW")
                    st.metric("🌍 CO2", f"{format_number(get_safe('taux_co2'))} g/kWh")
                    
                    st.caption(f"Updated: {latest.get('date', 'N/A')}")
                else:
                    st.error("No data in response")
            else:
                st.error(f"API Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            st.error("Request timed out")
        except Exception as e:
            st.error(f"Failed to fetch: {str(e)}")
    
    # Test connection
    st.subheader("Connection Status")
    if st.button("Test Connection"):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                if health.get("status") == "healthy":
                    st.success("✅ API Connected")
                    st.info(f"Eco2mix API: {health.get('eco2mix_api', 'unknown')}")
                else:
                    st.warning(f"⚠️ API Degraded: {health.get('status')}")
            else:
                st.error(f"❌ API Error: {response.status_code}")
        except:
            st.error("❌ Cannot connect to API")
    
    st.divider()
    st.info("Data from: RTE eco2mix API")

# Footer
st.sidebar.divider()
st.sidebar.info("""
### Troubleshooting
If you see null values:
1. The API might be temporarily unavailable
2. Try the "Get Latest Data" button
3. Check the console for errors
""")