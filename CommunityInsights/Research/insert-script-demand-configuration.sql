USE [CommunityInsights]
GO

INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('MaxLocationRadiusInMetre', '100', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('MaxActivitiesPerDemand', '10', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('StaffValidationSource', 'https://www.rms.com/staff/validate', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('TeamValidationSource', 'https://www.rms.com/team/validate', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('LocationVerificationSource', 'gazetter-connection-url', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('RMSConnectionURI', 'https://some-url', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('HRConnectionURI', 'https://some-url', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('CADConnectionURI', 'https://some-url', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('MaxRelatedPersons', '10', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('MaxRecordsReturned', '10', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('MaxLocationRadiusInMetre', '100', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('MapDefaultZoomLevel', '20', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('MapMinZoomLevel', '18', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('MapMaxZoomLevel', '23', null, GETUTCDATE())
INSERT INTO [dbo].[DemandConfiguration]([Config], [Value], [LastModifiedBy], [LastModifiedDate]) VALUES ('ApplicationTimeoutInSeconds', '600', null, GETUTCDATE())
GO


