Based on the Nutanix case study of Kreissparkasse Heilbronn and supporting documentation [[1]](https://portal.nutanix.com/page/documents/solutions/details?targetId=TN-2181-Citrix-Base-Image-Migrations-and-MCS-on-Nutanix-AHV:TN-2181-Citrix-Base-Image-Migrations-and-MCS-on-Nutanix-AHV), here's a **migration roadmap** for transitioning a Citrix infrastructure to a Nutanix-based environment:

### 🚀 **Citrix to Nutanix Migration Roadmap**

#### **Phase 1: Assessment & Planning**

1. **Inventory & Audit**

   * Catalog all Citrix components: Virtual Apps, Desktops, Delivery Controllers, StoreFront, Citrix ADC (NetScaler), etc.
   * Identify current hypervisor (e.g., VMware, Hyper-V) and storage architecture.
2. **Define Objectives**

   * Performance improvements, cost reduction, simplified management, disaster recovery, etc.
3. **Compatibility Check**

   * Ensure Citrix versions are compatible with Nutanix AHV.
   * Review Nutanix support for Machine Creation Services (MCS) and Citrix DaaS.
4. **Design Target Architecture**

   * Use Nutanix Prism for centralized management.
   * Plan for multi-cluster support if needed[[2]](https://www.nutanix.com/blog/multi-cluster-citrix-vdi-support-on-nutanix-ahv-with-prism).

### 🧭 **Phase 1: Assessment & Planning**

This foundational phase ensures a smooth and successful migration by thoroughly understanding the current environment and defining the future state.

#### 1. **Inventory & Audit**

* **Goal** : Gain a complete picture of the existing Citrix infrastructure.
* **Actions** :
* List all Citrix components: Delivery Controllers, StoreFront servers, Citrix ADC (NetScaler), Virtual Apps and Desktops.
* Document the current hypervisor (e.g., VMware vSphere, Microsoft Hyper-V).
* Identify storage systems, network topology, and integration points (e.g., Active Directory, licensing servers).
* Assess user profiles, application delivery methods, and endpoint types.

#### 2. **Define Objectives**

* **Goal** : Clarify what the organization wants to achieve with the migration.
* **Common Objectives** :
* Simplify infrastructure management.
* Improve performance and scalability.
* Reduce licensing and operational costs.
* Enhance disaster recovery and business continuity.
* Enable hybrid or multi-cloud capabilities.

#### 3. **Compatibility Check**

* **Goal** : Ensure all components are compatible with Nutanix AHV and supported by Citrix.
* **Actions** :
* Verify Citrix Virtual Apps and Desktops versions support Nutanix AHV.
* Check support for Machine Creation Services (MCS) on Nutanix.
* Review third-party integrations (e.g., antivirus, monitoring tools) for compatibility.

#### 4. **Design Target Architecture**

* **Goal** : Create a blueprint for the future Citrix-on-Nutanix environment.
* **Key Considerations** :
* Decide on the number of Nutanix clusters and node types.
* Plan for high availability, redundancy, and scalability.
* Define storage container layout and network segmentation.
* Design integration with Citrix Cloud (if applicable) or on-premises control plane.
* Include DR and backup strategies using Nutanix native tools (e.g., Leap, Mine).

---

---

#### **Phase 2: Infrastructure Preparation**

1. **Deploy Nutanix Cluster**

   * Install Nutanix AOS and AHV.
   * Configure networking, storage containers, and security policies.
2. **Integrate with Citrix**

   * Set up hosting connections in Citrix Studio to Nutanix AHV.
   * Validate communication between Citrix and Nutanix Prism.
3. **Image Management Setup**

   * Create or migrate base images to Nutanix.
   * Use Nutanix’s image replication and protection domains for DR [[1]](https://portal.nutanix.com/page/documents/solutions/details?targetId=TN-2181-Citrix-Base-Image-Migrations-and-MCS-on-Nutanix-AHV:TN-2181-Citrix-Base-Image-Migrations-and-MCS-on-Nutanix-AHV).

---

### 🏗️ **Phase 2: Infrastructure Preparation**

This phase focuses on setting up the Nutanix environment and ensuring it’s ready to host Citrix workloads.

#### 1. **Deploy Nutanix Cluster**

* **Goal** : Set up the foundational Nutanix infrastructure.
* **Actions** :
* Install Nutanix AOS (Acropolis Operating System) on physical nodes.
* Configure **AHV (Acropolis Hypervisor)** as the virtualization layer.
* Set up  **storage containers** ,  **networking (VLANs, IPAM)** , and  **cluster redundancy** .
* Use **Nutanix Foundation** for streamlined deployment and imaging.

#### 2. **Integrate with Citrix**

* **Goal** : Establish communication between Citrix and Nutanix.
* **Actions** :
* In  **Citrix Studio** , create a **hosting connection** to Nutanix AHV using the Prism Element or Prism Central API.
* Configure  **resource locations** ,  **machine catalogs** , and  **delivery groups** .
* Validate that Citrix can communicate with Nutanix for provisioning and power management.

#### 3. **Image Management Setup**

* **Goal** : Prepare base images for virtual desktops and apps.
* **Actions** :
* Create or migrate **golden images** to Nutanix AHV.
* Use **Citrix MCS (Machine Creation Services)** to manage image deployment.
* Optionally, leverage **Nutanix Calm** for automation or **Nutanix Files** for user profile storage.
* Set up **image replication** and **snapshot policies** for backup and DR.

---

This phase ensures that the Nutanix platform is fully operational and tightly integrated with Citrix before any workloads are migrated.

Would you like a visual diagram for this phase as well, or should we continue to  **Phase 3: Migration Execution** ?

---

#### **Phase 3: Migration Execution**

1. **Migrate Base Images**

   * Use Nutanix tools to replicate and register Citrix base images.
   * Validate image integrity and compatibility.
2. **Provision New Workloads**

   * Use MCS to deploy new VMs on Nutanix AHV.
   * Test pooled and persistent desktop scenarios.
3. **User Acceptance Testing**

   * Conduct pilot testing with a subset of users.
   * Monitor performance and user experience.

   ### 🔄 **Phase 3: Migration Execution**

   This phase involves moving Citrix workloads to the Nutanix platform and validating their performance and functionality.

   #### 1. **Migrate Base Images**


   * **Goal** : Ensure Citrix base images are available on Nutanix AHV.
   * **Actions** :
   * Convert existing VM templates or golden images to a format compatible with AHV (e.g., using Nutanix Image Service or manual import).
   * Upload and register images in Nutanix Prism.
   * Validate image integrity and ensure all required applications and agents (e.g., Citrix VDA, antivirus) are installed.

   #### 2. **Provision New Workloads**

   * **Goal** : Deploy virtual desktops and apps on Nutanix.
   * **Actions** :
   * Use **Citrix Machine Creation Services (MCS)** to create VMs on AHV from the base image.
   * Configure **machine catalogs** and **delivery groups** in Citrix Studio.
   * Assign users and test access to virtual desktops and published apps.

   #### 3. **User Acceptance Testing (UAT)**

   * **Goal** : Validate the new environment with real users.
   * **Actions** :
   * Select a pilot group of users to test the new environment.
   * Monitor performance, login times, application responsiveness, and user feedback.
   * Adjust configurations based on findings (e.g., resource allocation, policies).

   ---

   This phase is critical for ensuring that the new environment is stable, performant, and ready for broader adoption.

---

#### **Phase 4: Cutover & Optimization**

1. **Full Cutover**

   * Gradually transition all users to the Nutanix-based Citrix environment.
   * Decommission legacy infrastructure.
2. **Performance Tuning**

   * Use Nutanix Prism for real-time monitoring and optimization.
   * Adjust resource allocation based on usage patterns.
3. **Backup & DR Configuration**

   * Implement Nutanix-native DR and backup solutions.
   * Test failover and recovery procedures.

   ### 🚦 **Phase 4: Cutover & Optimization**

   This phase marks the transition from the legacy infrastructure to the new Nutanix-based Citrix environment and ensures it runs optimally.

   #### 1. **Full Cutover**


   * **Goal** : Transition all users and workloads to the Nutanix platform.
   * **Actions** :
   * Gradually migrate remaining users from the old environment to the new one.
   * Update DNS, load balancers, and access policies to point to the new infrastructure.
   * Monitor for any issues during the transition and provide support.

   #### 2. **Performance Tuning**

   * **Goal** : Optimize the environment for stability, speed, and efficiency.
   * **Actions** :
   * Use **Nutanix Prism** to monitor CPU, memory, and storage usage.
   * Adjust VM sizing, storage policies, and resource allocation based on real-world usage.
   * Enable **data locality** and **deduplication** features for better performance.

   #### 3. **Backup & DR Configuration**

   * **Goal** : Ensure data protection and business continuity.
   * **Actions** :
   * Implement **Nutanix native backup** (e.g., Nutanix Mine) or integrate with third-party solutions.
   * Configure **disaster recovery** using **Nutanix Leap** or replication to a secondary site.
   * Test backup and DR procedures to validate recovery time objectives (RTOs) and recovery point objectives (RPOs).

   ---

   This phase ensures that the new environment is not only live but also resilient, efficient, and ready for long-term operation.

---

#### **Phase 5: Post-Migration Support**

1. **Training & Documentation**
   * Train IT staff on Nutanix Prism and Citrix on AHV.
   * Document new processes and configurations.
2. **Ongoing Monitoring**
   * Set up alerts and dashboards in Prism.
   * Regularly review system health and performance.
   * 

---

References

[1] [Citrix Base Image Migrations and MCS Considerations on Nutanix AHV](https://portal.nutanix.com/page/documents/solutions/details?targetId=TN-2181-Citrix-Base-Image-Migrations-and-MCS-on-Nutanix-AHV:TN-2181-Citrix-Base-Image-Migrations-and-MCS-on-Nutanix-AHV)

[2] [Multi-Cluster Citrix VDI Support on Nutanix AHV with Prism](https://www.nutanix.com/blog/multi-cluster-citrix-vdi-support-on-nutanix-ahv-with-prism)

### **Phase 4: Cutover & Optimization**

This phase marks the transition from the legacy infrastructure to the new Nutanix-based Citrix environment and ensures it runs optimally.

#### 1. **Full Cutover**

* **Goal** : Transition all users and workloads to the Nutanix platform.
* **Actions** :
* Gradually migrate remaining users from the old environment to the new one.
* Update DNS, load balancers, and access policies to point to the new infrastructure.
* Monitor for any issues during the transition and provide support.

#### 2. **Performance Tuning**

* **Goal** : Optimize the environment for stability, speed, and efficiency.
* **Actions** :
* Use **Nutanix Prism** to monitor CPU, memory, and storage usage.
* Adjust VM sizing, storage policies, and resource allocation based on real-world usage.
* Enable **data locality** and **deduplication** features for better performance.

#### 3. **Backup & DR Configuration**

* **Goal** : Ensure data protection and business continuity.
* **Actions** :
* Implement **Nutanix native backup** (e.g., Nutanix Mine) or integrate with third-party solutions.
* Configure **disaster recovery** using **Nutanix Leap** or replication to a secondary site.
* Test backup and DR procedures to validate recovery time objectives (RTOs) and recovery point objectives (RPOs).

---

This phase ensures that the new environment is not only live but also resilient, efficient, and ready for long-term operation.

### **Phase 4: Cutover & Optimization**

This phase marks the transition from the legacy infrastructure to the new Nutanix-based Citrix environment and ensures it runs optimally.

#### 1. **Full Cutover**

* **Goal** : Transition all users and workloads to the Nutanix platform.
* **Actions** :
* Gradually migrate remaining users from the old environment to the new one.
* Update DNS, load balancers, and access policies to point to the new infrastructure.
* Monitor for any issues during the transition and provide support.

#### 2. **Performance Tuning**

* **Goal** : Optimize the environment for stability, speed, and efficiency.
* **Actions** :
* Use **Nutanix Prism** to monitor CPU, memory, and storage usage.
* Adjust VM sizing, storage policies, and resource allocation based on real-world usage.
* Enable **data locality** and **deduplication** features for better performance.

#### 3. **Backup & DR Configuration**

* **Goal** : Ensure data protection and business continuity.
* **Actions** :
* Implement **Nutanix native backup** (e.g., Nutanix Mine) or integrate with third-party solutions.
* Configure **disaster recovery** using **Nutanix Leap** or replication to a secondary site.
* Test backup and DR procedures to validate recovery time objectives (RTOs) and recovery point objectives (RPOs).

---

This phase ensures that the new environment is not only live but also resilient, efficient, and ready for long-term operation.

### 🛠️ **Phase 5: Post-Migration Support**

This phase focuses on operational readiness, continuous improvement, and ensuring the IT team is equipped to manage the new environment effectively.

#### 1. **Training & Documentation**

* **Goal** : Empower IT staff and ensure knowledge transfer.
* **Actions** :
* Provide training on  **Nutanix Prism** ,  **AHV** , and  **Citrix integration** .
* Document new architecture, configurations, and operational procedures.
* Create runbooks for common tasks (e.g., VM provisioning, troubleshooting, DR failover).

#### 2. **Ongoing Monitoring**

* **Goal** : Maintain performance, availability, and security.
* **Actions** :
* Set up **alerts and dashboards** in Nutanix Prism for proactive monitoring.
* Regularly review  **performance metrics** ,  **capacity planning** , and  **user feedback** .
* Schedule periodic  **health checks** ,  **patching** , and  **security audits** .

---

This final phase ensures that your organization is not only running on a modern, high-performance platform but is also prepared to maintain and evolve it over time.

### 🛠️ **Phase 5: Post-Migration Support**

This phase focuses on operational readiness, continuous improvement, and ensuring the IT team is equipped to manage the new environment effectively.

#### 1. **Training & Documentation**

* **Goal** : Empower IT staff and ensure knowledge transfer.
* **Actions** :
* Provide training on  **Nutanix Prism** ,  **AHV** , and  **Citrix integration** .
* Document new architecture, configurations, and operational procedures.
* Create runbooks for common tasks (e.g., VM provisioning, troubleshooting, DR failover).

#### 2. **Ongoing Monitoring**

* **Goal** : Maintain performance, availability, and security.
* **Actions** :
* Set up **alerts and dashboards** in Nutanix Prism for proactive monitoring.
* Regularly review  **performance metrics** ,  **capacity planning** , and  **user feedback** .
* Schedule periodic  **health checks** ,  **patching** , and  **security audits** .

---

This final phase ensures that your organization is not only running on a modern, high-performance platform but is also prepared to maintain and evolve it over time.
